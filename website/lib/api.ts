export type NewsArticle = {
  id: number;
  title: string;
  summary: string | null;
  content: string | null;
  category: string;
  image_url: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type NewsListResponse = {
  status: string;
  items: NewsArticle[];
};

export type CreateNewsInput = {
  title: string;
  category: string;
  summary: string | null;
  content: string | null;
};

export function getPublicApiUrl() {
  return process.env.NEXT_PUBLIC_ANASTARIA_API_URL?.replace(/\/$/, "") ?? null;
}

export async function createNews(input: CreateNewsInput) {
  const apiUrl = getPublicApiUrl();

  if (!apiUrl) {
    throw new Error("NEXT_PUBLIC_ANASTARIA_API_URL is not configured.");
  }

  const response = await fetch(`${apiUrl}/news`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error("The news item could not be published.");
  }

  return (await response.json()) as NewsArticle;
}

export async function getNews(signal?: AbortSignal) {
  const apiUrl = getPublicApiUrl();
  if (!apiUrl) throw new Error("NEXT_PUBLIC_ANASTARIA_API_URL is not configured.");
  const response = await fetch(`${apiUrl}/news`, { signal });
  if (!response.ok) throw new Error("News could not be loaded.");
  return (await response.json()) as NewsListResponse;
}

export type GameEvent = { id: number; slug: string; translations: Record<string, { title?: string; description?: string }>; schedule: string; timezone: string; category: string; reward_summary: string | null; active: boolean };
export type EventsResponse = { status: string; server_time: string; items: GameEvent[] };
export type SiteSetting = { key: string; value: Record<string, string | boolean | null>; updated_at: string };

export async function getEvents(signal?: AbortSignal) {
  const apiUrl = getPublicApiUrl(); if (!apiUrl) throw new Error("API is not configured.");
  const response = await fetch(`${apiUrl}/events`, { signal }); if (!response.ok) throw new Error("Events could not be loaded.");
  return (await response.json()) as EventsResponse;
}

export async function createEvent(input: Omit<GameEvent, "id">) {
  const apiUrl = getPublicApiUrl(); if (!apiUrl) throw new Error("API is not configured.");
  const response = await fetch(`${apiUrl}/events`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials:"include", body: JSON.stringify(input) });
  if (!response.ok) throw new Error("Event could not be saved."); return (await response.json()) as GameEvent;
}

export async function getSiteSettings(signal?: AbortSignal) {
  const apiUrl = getPublicApiUrl(); if (!apiUrl) throw new Error("API is not configured.");
  const response = await fetch(`${apiUrl}/site-settings`, { signal }); if (!response.ok) throw new Error("Contact settings could not be loaded.");
  return (await response.json()) as { status: string; items: SiteSetting[] };
}

export async function updateSiteSetting(key: string, value: SiteSetting["value"]) {
  const apiUrl = getPublicApiUrl(); if (!apiUrl) throw new Error("API is not configured.");
  const response = await fetch(`${apiUrl}/site-settings/${encodeURIComponent(key)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, credentials:"include", body: JSON.stringify({ value }) });
  if (!response.ok) throw new Error("Setting could not be saved."); return (await response.json()) as SiteSetting;
}

export type LiveServerStatus = { status: "online" | "offline" | "unconfigured"; players_online: number | null; version: string | null; season: number | null; episode: number | null; game_servers: number; checked_at: string };
export async function getServerStatus(signal?: AbortSignal) { const apiUrl=getPublicApiUrl(); if(!apiUrl) throw new Error("API is not configured."); const response=await fetch(`${apiUrl}/server/status`,{signal,cache:"no-store"}); if(!response.ok) throw new Error("Server status unavailable."); return (await response.json()) as LiveServerStatus; }

export type CurrencyDefinition = { id:number; code:string; name:string; kind:string; icon:string|null; purchasable:boolean; active:boolean; sort_order:number };
export type CoinPackage = { id:number; title:string; description:string|null; currency_code:string; coin_amount:number; bonus_amount:number; price_minor:number; settlement_currency:string; image_url:string|null; featured:boolean; active:boolean; sort_order:number };
export type ShopProduct = { id:number; title:string; openmu_item_id:string|null; description:string|null; category:string; currency_code:string; price_amount:number; selected_options:Record<string,number|boolean|string|string[]>; discount_percent:number; discount_starts_at:string|null; discount_ends_at:string|null; delivery_code:string|null; image_url:string|null; featured:boolean; active:boolean; sort_order:number };
export type GameItemPower = { attribute:string; base_value:number; aggregate_type:number; level_bonuses:{level:number;value:number}[] };
export type GameItemCatalogItem = { id:string; name:string; group:number; number:number; width:number; height:number; maximum_item_level:number; durability:number; maximum_sockets:number; slot:string|null; category:string; allowed_classes:string[]; available_options:string[]; base_power_ups:GameItemPower[] };
export type CommerceCatalog = { status:string; currencies:CurrencyDefinition[]; coin_packages:CoinPackage[]; products:ShopProduct[] };
async function commerceRequest<T>(path:string, options?:RequestInit) { const apiUrl=getPublicApiUrl(); if(!apiUrl) throw new Error("API is not configured."); const response=await fetch(`${apiUrl}${path}`,{...options,credentials:"include"}); if(!response.ok){const data=await response.json();throw new Error(typeof data.detail==="string"?data.detail:"Commerce data could not be saved.");} if(response.status===204)return undefined as T; return (await response.json()) as T; }
export function getCommerceCatalog(signal?:AbortSignal) { return commerceRequest<CommerceCatalog>("/commerce/catalog",{signal,cache:"no-store"}); }
export function createCurrency(input:Omit<CurrencyDefinition,"id">) { return commerceRequest<CurrencyDefinition>("/commerce/currencies",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)}); }
export function createCoinPackage(input:Omit<CoinPackage,"id">) { return commerceRequest<CoinPackage>("/commerce/coin-packages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)}); }
export function createShopProduct(input:Omit<ShopProduct,"id">) { return commerceRequest<ShopProduct>("/commerce/products",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)}); }
export function deleteShopProduct(id:number) { return commerceRequest<void>(`/commerce/products/${id}`,{method:"DELETE"}); }
export function searchGameItems(search:string,signal?:AbortSignal,category="",limit=100) { return commerceRequest<GameItemCatalogItem[]>(`/game/items?search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}&limit=${limit}`,{signal,cache:"no-store"}); }
export function getGameItemImageUrl(item:Pick<GameItemCatalogItem,"group"|"number">,level=0,variant:"normal"|"excellent"|"ancient"="normal"){const apiUrl=getPublicApiUrl();return apiUrl?`${apiUrl}/game/items/image?group=${item.group}&number=${item.number}&level=${level}&variant=${variant}`:"";}

async function authRequest<T>(path:string,options?:RequestInit){const apiUrl=getPublicApiUrl();if(!apiUrl)throw new Error("API is not configured.");const response=await fetch(`${apiUrl}/auth${path}`,{...options,credentials:"include"});const data=await response.json();if(!response.ok){const detail=typeof data.detail==="string"?data.detail:Array.isArray(data.detail)?data.detail.map((item:{msg?:string})=>item.msg).filter(Boolean).join(" "):"Authentication request failed.";throw new Error(detail);}return data as T;}
export function getCaptcha(){return authRequest<{challenge_id:string;question:string}>("/captcha");}
export function registerAccount(input:{username:string;email:string;password:string;language:string;security_question:string;security_answer:string;challenge_id:string;answer:string}){return authRequest<{status:string;message:string}>("/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)});}
export function loginAccount(username:string,password:string){return authRequest<{status:string}>("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,password})});}
export function logoutAccount(){return authRequest<{status:string}>("/logout",{method:"POST"});}
export function requestPasswordReset(email:string,challenge_id:string,answer:string){return authRequest<{message:string}>("/password-reset/request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,challenge_id,answer})});}
export function confirmPasswordReset(token:string,password:string){return authRequest<{status:string}>("/password-reset/confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token,password})});}
export function requestSecurityReset(username:string,email:string,challenge_id:string,answer:string){return authRequest<{token:string;question:string;expires_in:number}>("/password-reset/security/request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,email,challenge_id,answer})});}
export function confirmSecurityReset(token:string,security_answer:string,password:string){return authRequest<{status:string;message:string}>("/password-reset/security/confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token,security_answer,password})});}
export type AccountCharacter={id:string;name:string;character_class:string;map_name:string;experience:number;master_experience:number;level:number;master_level:number;resets:number};
export type AccountMe={id:string;username:string;email:string;language:string;role:"player"|"game_master";profile:{display_name:string;country_code:string|null;avatar_url:string|null;bio:string|null}|null;characters:AccountCharacter[]};
export function getMe(){return authRequest<AccountMe>("/me");}
export function updateProfile(input:{display_name:string;country_code:string|null;avatar_url:string|null;bio:string|null}){return authRequest<AccountMe["profile"]>("/profile",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)});}
