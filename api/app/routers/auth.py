import hashlib
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import SessionLocal
from app.models.auth import AccountSecurityQuestion, CaptchaChallenge, PasswordResetToken, WebProfile, WebSession

router = APIRouter(prefix=f"{settings.api_prefix}/auth", tags=["auth"])

def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()

def digest(value:str)->str: return hashlib.sha256(value.encode()).hexdigest()
def security_answer_material(value:str)->bytes: return digest(value.strip().casefold()).encode()

class CaptchaAnswer(BaseModel): challenge_id:str; answer:str
SECURITY_QUESTIONS = {
    "first_pet": "What was the name of your first pet?",
    "birth_city": "In what city were you born?",
    "childhood_friend": "What was the first name of your childhood best friend?",
    "first_school": "What was the name of your first school?",
}

class PasswordRules(BaseModel):
    password: str = Field(min_length=10, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.islower() for char in value): raise ValueError("Password must contain a lowercase letter")
        if not any(char.isupper() for char in value): raise ValueError("Password must contain an uppercase letter")
        if not any(char.isdigit() for char in value): raise ValueError("Password must contain a number")
        if not any(not char.isalnum() for char in value): raise ValueError("Password must contain a special character")
        return value

class RegisterInput(CaptchaAnswer, PasswordRules):
    username: str
    email: EmailStr
    language: str = "en"
    security_question: str
    security_answer: str = Field(min_length=3,max_length=72)

    @field_validator("security_question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if value not in SECURITY_QUESTIONS: raise ValueError("Select a valid security question")
        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if len(value) < 4: raise ValueError("Username must contain at least 4 characters")
        if len(value) > 10: raise ValueError("Username cannot contain more than 10 characters")
        if not all(char.isascii() and (char.isalnum() or char == "_") for char in value): raise ValueError("Username may contain only letters, numbers and underscore")
        return value
class LoginInput(BaseModel): username:str; password:str
class ProfileInput(BaseModel): display_name:str=Field(min_length=2,max_length=40); country_code:str|None=Field(default=None,min_length=2,max_length=2); avatar_url:str|None=None; bio:str|None=Field(default=None,max_length=500)
class ResetRequest(CaptchaAnswer): email:EmailStr
class ResetConfirm(PasswordRules): token:str
class SecurityResetRequest(CaptchaAnswer): username:str; email:EmailStr
class SecurityResetConfirm(PasswordRules): token:str; security_answer:str=Field(min_length=3,max_length=72)

def verify_captcha(db:Session, challenge_id:str, answer:str):
    item=db.get(CaptchaChallenge,challenge_id); now=datetime.now(timezone.utc)
    if not item or item.used or item.expires_at < now or not secrets.compare_digest(item.answer_hash,digest(f"{challenge_id}:{answer.strip()}")):
        raise HTTPException(400,"Invalid or expired verification challenge")
    item.used=True

def account_from_session(db:Session, token:str|None):
    if not token: raise HTTPException(401,"Authentication required")
    session=db.scalar(select(WebSession).where(WebSession.token_hash==digest(token),WebSession.expires_at>datetime.now(timezone.utc)))
    if not session: raise HTTPException(401,"Session expired")
    account=db.execute(text('SELECT "Id"::text AS id,"LoginName" AS username,"EMail" AS email,"LanguageIsoCode" AS language,"State" AS state FROM data."Account" WHERE "Id"::text=:id'),{"id":session.account_id}).mappings().first()
    if not account: raise HTTPException(401,"Account unavailable")
    return account

def account_role(state:int)->str:
    return "game_master" if state in (2,3) else "player"

def require_game_master(anastaria_session:str|None=Cookie(default=None),db:Session=Depends(get_db)):
    account=account_from_session(db,anastaria_session)
    if account_role(account["state"]) != "game_master": raise HTTPException(403,"Game Master access required")
    return account

@router.get("/captcha")
def captcha(db:Session=Depends(get_db)):
    left=secrets.randbelow(8)+2;right=secrets.randbelow(8)+2;challenge_id=secrets.token_urlsafe(24)
    db.add(CaptchaChallenge(id=challenge_id,answer_hash=digest(f"{challenge_id}:{left+right}"),expires_at=datetime.now(timezone.utc)+timedelta(minutes=5),used=False));db.commit()
    return {"challenge_id":challenge_id,"question":f"{left} + {right} = ?","expires_in":300}

@router.post("/register",status_code=201)
def register(payload:RegisterInput,response:Response,db:Session=Depends(get_db)):
    verify_captcha(db,payload.challenge_id,payload.answer); username=payload.username.strip();email=str(payload.email).lower()
    if db.execute(text('SELECT 1 FROM data."Account" WHERE lower("LoginName")=lower(:u)'),{"u":username}).scalar(): raise HTTPException(409,"This username is already in use")
    if db.execute(text('SELECT 1 FROM data."Account" WHERE lower("EMail")=lower(:e)'),{"e":email}).scalar(): raise HTTPException(409,"This email address is already in use")
    account_id=str(uuid.uuid4());password_hash=bcrypt.hashpw(payload.password.encode(),bcrypt.gensalt(rounds=12)).decode()
    db.execute(text('INSERT INTO data."Account" ("Id","LoginName","PasswordHash","SecurityCode","EMail","RegistrationDate","State","TimeZone","VaultPassword","IsVaultExtended","IsTemplate","LanguageIsoCode","IsBot") VALUES (:id,:u,:p,\'\',:e,:now,0,0,\'\',false,false,:lang,false)'),{"id":account_id,"u":username,"p":password_hash,"e":email,"now":datetime.now(timezone.utc),"lang":payload.language[:5]})
    db.add(WebProfile(account_id=account_id,display_name=username,country_code=None,avatar_url=None,bio=None,created_at=datetime.now(timezone.utc),updated_at=datetime.now(timezone.utc)))
    now=datetime.now(timezone.utc);db.add(AccountSecurityQuestion(account_id=account_id,question=SECURITY_QUESTIONS[payload.security_question],answer_hash=bcrypt.hashpw(security_answer_material(payload.security_answer),bcrypt.gensalt(rounds=12)).decode(),created_at=now,updated_at=now));db.commit()
    return {"status":"created","message":"Account created. You can use it on the website and in the game."}

@router.post("/login")
def login(payload:LoginInput,response:Response,db:Session=Depends(get_db)):
    row=db.execute(text('SELECT "Id"::text AS id,"PasswordHash" AS password_hash,"State" AS state FROM data."Account" WHERE lower("LoginName")=lower(:u)'),{"u":payload.username.strip()}).mappings().first()
    valid=bool(row) and bcrypt.checkpw(payload.password.encode(),row["password_hash"].encode())
    if not valid or row["state"] in (4,5): raise HTTPException(401,"Invalid username or password")
    token=secrets.token_urlsafe(48);now=datetime.now(timezone.utc);db.add(WebSession(account_id=row["id"],token_hash=digest(token),created_at=now,expires_at=now+timedelta(days=7)));db.commit()
    response.set_cookie("anastaria_session",token,max_age=604800,httponly=True,samesite="lax",secure=settings.environment=="production",path="/")
    return {"status":"ok"}

@router.post("/logout")
def logout(response:Response,anastaria_session:str|None=Cookie(default=None),db:Session=Depends(get_db)):
    if anastaria_session: db.query(WebSession).filter(WebSession.token_hash==digest(anastaria_session)).delete();db.commit()
    response.delete_cookie("anastaria_session",path="/");return {"status":"ok"}

@router.get("/me")
def me(anastaria_session:str|None=Cookie(default=None),db:Session=Depends(get_db)):
    account=account_from_session(db,anastaria_session);profile=db.get(WebProfile,account["id"])
    characters=db.execute(text('''
        SELECT c."Id"::text AS id,c."Name" AS name,COALESCE(cc."Name",'Unknown') AS character_class,
            COALESCE(m."Name",'Unknown') AS map_name,c."Experience" AS experience,c."MasterExperience" AS master_experience,
            COALESCE(MAX(s."Value") FILTER (WHERE ad."Designation"='Level'),0)::int AS level,
            COALESCE(MAX(s."Value") FILTER (WHERE ad."Designation"='Master Level'),0)::int AS master_level,
            COALESCE(MAX(s."Value") FILTER (WHERE ad."Designation"='Resets'),0)::int AS resets
        FROM data."Character" c
        LEFT JOIN config."CharacterClass" cc ON cc."Id"=c."CharacterClassId"
        LEFT JOIN config."GameMapDefinition" m ON m."Id"=c."CurrentMapId"
        LEFT JOIN data."StatAttribute" s ON s."CharacterId"=c."Id"
        LEFT JOIN config."AttributeDefinition" ad ON ad."Id"=s."DefinitionId"
        WHERE c."AccountId"::text=:id
        GROUP BY c."Id",c."Name",cc."Name",m."Name",c."Experience",c."MasterExperience",c."CreateDate"
        ORDER BY c."CreateDate"
    '''),{"id":account["id"]}).mappings().all()
    result=dict(account);result["role"]=account_role(result.pop("state"));result["profile"]=profile;result["characters"]=[dict(character) for character in characters]
    return result

@router.put("/profile")
def update_profile(payload:ProfileInput,anastaria_session:str|None=Cookie(default=None),db:Session=Depends(get_db)):
    account=account_from_session(db,anastaria_session);profile=db.get(WebProfile,account["id"]);now=datetime.now(timezone.utc)
    if profile is None: profile=WebProfile(account_id=account["id"],created_at=now,updated_at=now,**payload.model_dump());db.add(profile)
    else:
        for key,value in payload.model_dump().items():setattr(profile,key,value)
        profile.updated_at=now
    db.commit();db.refresh(profile);return profile

@router.post("/password-reset/request")
def request_reset(payload:ResetRequest,db:Session=Depends(get_db)):
    verify_captcha(db,payload.challenge_id,payload.answer);account=db.execute(text('SELECT "Id"::text AS id,"EMail" AS email FROM data."Account" WHERE lower("EMail")=lower(:e)'),{"e":str(payload.email)}).mappings().first()
    if account and settings.smtp_host and settings.smtp_from:
        token=secrets.token_urlsafe(48);db.add(PasswordResetToken(account_id=account["id"],token_hash=digest(token),expires_at=datetime.now(timezone.utc)+timedelta(minutes=30),used=False,purpose="email",attempts=0));db.commit();message=EmailMessage();message["Subject"]="ANASTARIA password reset";message["From"]=settings.smtp_from;message["To"]=account["email"];message.set_content(f"Reset your password: {settings.website_url}/reset-password?token={token}")
        with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as smtp: smtp.starttls();smtp.login(settings.smtp_username,settings.smtp_password);smtp.send_message(message)
    return {"status":"ok","message":"If the address belongs to an account, reset instructions will be sent."}

@router.post("/password-reset/confirm")
def confirm_reset(payload:ResetConfirm,db:Session=Depends(get_db)):
    item=db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash==digest(payload.token),PasswordResetToken.purpose=="email",PasswordResetToken.used.is_(False),PasswordResetToken.expires_at>datetime.now(timezone.utc)))
    if not item: raise HTTPException(400,"Invalid or expired reset token")
    db.execute(text('UPDATE data."Account" SET "PasswordHash"=:p WHERE "Id"::text=:id'),{"p":bcrypt.hashpw(payload.password.encode(),bcrypt.gensalt(rounds=12)).decode(),"id":item.account_id});item.used=True;db.query(WebSession).filter(WebSession.account_id==item.account_id).delete();db.commit();return {"status":"ok"}

@router.post("/password-reset/security/request")
def request_security_reset(payload:SecurityResetRequest,db:Session=Depends(get_db)):
    verify_captcha(db,payload.challenge_id,payload.answer)
    account=db.execute(text('SELECT "Id"::text AS id FROM data."Account" WHERE lower("LoginName")=lower(:u) AND lower("EMail")=lower(:e)'),{"u":payload.username.strip(),"e":str(payload.email).lower()}).mappings().first()
    credential=db.get(AccountSecurityQuestion,account["id"]) if account else None
    if not credential: raise HTTPException(404,"No account with this username and email has a security question")
    token=secrets.token_urlsafe(48);db.add(PasswordResetToken(account_id=account["id"],token_hash=digest(token),expires_at=datetime.now(timezone.utc)+timedelta(minutes=10),used=False,purpose="security",attempts=0));db.commit()
    return {"token":token,"question":credential.question,"expires_in":600}

@router.post("/password-reset/security/confirm")
def confirm_security_reset(payload:SecurityResetConfirm,db:Session=Depends(get_db)):
    item=db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash==digest(payload.token),PasswordResetToken.purpose=="security",PasswordResetToken.used.is_(False),PasswordResetToken.expires_at>datetime.now(timezone.utc)))
    if not item: raise HTTPException(400,"Invalid or expired recovery request")
    credential=db.get(AccountSecurityQuestion,item.account_id)
    valid=credential and bcrypt.checkpw(security_answer_material(payload.security_answer),credential.answer_hash.encode())
    if not valid:
        item.attempts += 1
        if item.attempts >= 5: item.used = True
        db.commit()
        raise HTTPException(400,"The security answer is incorrect")
    db.execute(text('UPDATE data."Account" SET "PasswordHash"=:p WHERE "Id"::text=:id'),{"p":bcrypt.hashpw(payload.password.encode(),bcrypt.gensalt(rounds=12)).decode(),"id":item.account_id});item.used=True;db.query(WebSession).filter(WebSession.account_id==item.account_id).delete();db.commit()
    return {"status":"ok","message":"Password changed. You can now sign in."}
