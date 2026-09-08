from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware



from app.config import settings

from app.routers import auth, commerce, marketplace, news, rankings, server, site_content



app = FastAPI(title="ANASTARIA API", version="1.0.0")



# CORS Configuration

app.add_middleware(

    CORSMiddleware,

    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



@app.get("/")

def read_root():

    return {"message": "ANASTARIA API"}



app.include_router(server.router)

app.include_router(news.router)

app.include_router(rankings.router)
app.include_router(site_content.router)
app.include_router(commerce.router)
app.include_router(auth.router)
app.include_router(marketplace.router)
