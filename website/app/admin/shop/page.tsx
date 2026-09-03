"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createCoinPackage,
  createCurrency,
  createShopProduct,
  deleteShopProduct,
  getCommerceCatalog,
  getGameItemImageUrl,
  searchGameItems,
  type GameItemCatalogItem,
  type ShopProduct,
} from "@/lib/api";

const categories = [
  "Weapons",
  "Shields",
  "Helms",
  "Armors",
  "Pants",
  "Gloves",
  "Boots",
  "Wings",
  "Accessories",
  "Pets",
  "Buffs & Consumables",
  "Jewels & Special",
  "Miscellaneous",
];
const field =
  "mt-2 w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 text-sm outline-none focus:border-amber-300/60";
function itemAspectRatio(item?: Pick<GameItemCatalogItem, "width" | "height">) {
  const width = Math.max(1, item?.width ?? 1);
  const height = Math.max(1, item?.height ?? 1);
  return `${width} / ${height}`;
}

export default function AdminShopPage() {
  const [category, setCategory] = useState("Weapons");
  const [search, setSearch] = useState("");
  const [items, setItems] = useState<GameItemCatalogItem[]>([]);
  const [products, setProducts] = useState<ShopProduct[]>([]);
  const [selected, setSelected] = useState<GameItemCatalogItem | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loadItems = useCallback(
    async (term: string, selectedCategory: string) => {
      setLoading(true);
      setError(null);
      try {
        setItems(await searchGameItems(term, undefined, selectedCategory, 250));
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "OpenMU catalog unavailable.",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );
  const loadProducts = useCallback(async () => {
    try {
      setProducts((await getCommerceCatalog()).products);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Published products could not be loaded.",
      );
    }
  }, []);
  // Loading the external OpenMU catalog is the synchronization performed by this effect.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    void loadItems("", category);
    void loadProducts();
  }, [category, loadItems, loadProducts]);
  function chooseCategory(nextCategory: string) {
    setCategory(nextCategory);
    setSelected(null);
    setOptions([]);
  }
  function toggleOption(option: string) {
    setOptions((current) =>
      current.includes(option)
        ? current.filter((value) => value !== option)
        : [...current, option],
    );
  }
  async function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) {
      setError("Select an item first.");
      return;
    }
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(null);
    setMessage(null);
    try {
      await createShopProduct({
        title: selected.name,
        openmu_item_id: selected.id,
        description: String(data.get("description")) || null,
        category: selected.category,
        currency_code: String(data.get("currency_code")).toUpperCase(),
        price_amount: Number(data.get("price_amount")),
        selected_options: { level: Number(data.get("item_level")), options },
        discount_percent: Number(data.get("discount_percent")) || 0,
        discount_starts_at: null,
        discount_ends_at: null,
        delivery_code: `openmu:${selected.group}:${selected.number}`,
        image_url: null,
        featured: Boolean(data.get("featured")),
        active: true,
        sort_order: 0,
      });
      setMessage(`${selected.name} was added to the shop.`);
      form.reset();
      setOptions([]);
      await loadProducts();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Product could not be published.",
      );
    }
  }
  async function removeProduct(product: ShopProduct) {
    if (!window.confirm(`Delete ${product.title} from the shop?`)) return;
    setError(null);
    try {
      await deleteShopProduct(product.id);
      setProducts((current) =>
        current.filter((item) => item.id !== product.id),
      );
      setMessage(`${product.title} was deleted from the shop.`);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Product could not be deleted.",
      );
    }
  }
  async function saveCurrency(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createCurrency({
        code: String(data.get("code")).toUpperCase(),
        name: String(data.get("name")),
        kind: "virtual",
        icon: null,
        purchasable: Boolean(data.get("purchasable")),
        active: true,
        sort_order: 0,
      });
      form.reset();
      setMessage("Currency saved.");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Currency could not be saved.",
      );
    }
  }
  async function savePackage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createCoinPackage({
        title: String(data.get("title")),
        description: null,
        currency_code: String(data.get("currency_code")).toUpperCase(),
        coin_amount: Number(data.get("coin_amount")),
        bonus_amount: Number(data.get("bonus_amount")) || 0,
        price_minor: Math.round(Number(data.get("price")) * 100),
        settlement_currency: "EUR",
        image_url: null,
        featured: Boolean(data.get("featured")),
        active: true,
        sort_order: 0,
      });
      form.reset();
      setMessage("Coin package saved.");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Package could not be saved.",
      );
    }
  }

  return (
    <main className="min-h-screen bg-[#07080b] px-5 py-10 text-white">
      <div className="mx-auto max-w-[1500px]">
        <header className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="mu-kicker">GM SHOP MANAGER</p>
            <h1 className="mt-2 text-4xl font-black">Add an item in 3 steps</h1>
            <p className="mt-3 text-sm text-gray-500">
              Choose a category, click the real OpenMU item, then set its price.
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard"
              className="rounded border border-white/10 px-4 py-2 text-sm text-gray-300"
            >
              Dashboard
            </Link>
            <Link
              href="/shop"
              className="rounded bg-amber-400 px-4 py-2 text-sm font-black text-black"
            >
              View shop
            </Link>
          </div>
        </header>
        {message && (
          <p className="mt-6 rounded border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-300">
            {message}
          </p>
        )}
        {error && (
          <p className="mt-6 rounded border border-red-400/20 bg-red-400/10 p-4 text-red-300">
            {error}
          </p>
        )}
        <section className="mt-8 rounded-xl border border-white/10 bg-white/[.025] p-5">
          <p className="text-xs font-black uppercase tracking-wider text-gray-500">
            1. Category
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {categories.map((item) => (
              <button
                key={item}
                onClick={() => chooseCategory(item)}
                className={`rounded-lg px-4 py-2 text-xs font-bold ${category === item ? "bg-amber-400 text-black" : "border border-white/10 bg-black/30 text-gray-400 hover:text-white"}`}
              >
                {item}
              </button>
            ))}
          </div>
          <div className="mt-5 flex gap-3">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void loadItems(search, category);
                }
              }}
              placeholder={`Search in ${category}`}
              className={field}
            />
            <button
              onClick={() => void loadItems(search, category)}
              className="mt-2 rounded-lg border border-amber-300/30 px-5 text-sm font-bold text-amber-300"
            >
              Search
            </button>
          </div>
        </section>
        <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_380px]">
          <section className="rounded-xl border border-white/10 bg-white/[.025] p-5">
            <div className="flex justify-between">
              <p className="text-xs font-black uppercase tracking-wider text-gray-500">
                2. Choose item
              </p>
              <span className="text-xs text-gray-600">
                {loading ? "Loading…" : `${items.length} items`}
              </span>
            </div>
            <div className="mt-4 grid max-h-[720px] grid-cols-2 gap-3 overflow-y-auto pr-2 sm:grid-cols-3 lg:grid-cols-4">
              {items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    setSelected(item);
                    setOptions([]);
                  }}
                  className={`group rounded-xl border p-3 text-left transition ${selected?.id === item.id ? "border-amber-300 bg-amber-300/10" : "border-white/10 bg-black/25 hover:border-white/25"}`}
                >
                  <div
                    className="flex items-center justify-center overflow-hidden rounded-lg bg-[radial-gradient(circle,rgba(245,180,60,.13),transparent_65%)]"
                    style={{ aspectRatio: itemAspectRatio(item) }}
                  >
                    <img
                      src={getGameItemImageUrl(item)}
                      alt={item.name}
                      loading="lazy"
                      className="h-full w-full object-contain transition group-hover:scale-105"
                    />
                  </div>
                  <strong className="mt-3 block text-sm text-amber-100">
                    {item.name}
                  </strong>
                  <span className="mt-1 block text-[10px] text-gray-600">
                    Group {item.group} · #{item.number}
                  </span>
                </button>
              ))}
            </div>
          </section>
          <aside className="xl:sticky xl:top-24 xl:self-start">
            <form
              onSubmit={publish}
              className="rounded-xl border border-amber-300/20 bg-[#11100e] p-6"
            >
              <p className="text-xs font-black uppercase tracking-wider text-gray-500">
                3. Configure & publish
              </p>
              {selected ? (
                <>
                  <div className="mt-5 flex items-center gap-4">
                    <div
                      className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-[radial-gradient(circle,rgba(245,180,60,.13),transparent_65%)]"
                      style={{ aspectRatio: itemAspectRatio(selected) }}
                    >
                      <img
                        src={getGameItemImageUrl(selected)}
                        alt={selected.name}
                        className="h-full w-full object-contain"
                      />
                    </div>
                    <div>
                      <p className="text-xs text-amber-400">
                        {selected.category}
                      </p>
                      <h2 className="mt-1 text-xl font-black">
                        {selected.name}
                      </h2>
                      <p className="mt-1 text-xs text-gray-600">
                        {selected.width}×{selected.height} · durability{" "}
                        {selected.durability}
                      </p>
                    </div>
                  </div>
                  <div className="mt-6 space-y-4">
                    <label className="block text-xs font-bold text-gray-400">
                      Price
                      <input
                        name="price_amount"
                        type="number"
                        min="1"
                        required
                        className={field}
                      />
                    </label>
                    <label className="block text-xs font-bold text-gray-400">
                      Currency
                      <input
                        name="currency_code"
                        required
                        defaultValue="AC"
                        maxLength={32}
                        className={field}
                      />
                    </label>
                    <label className="block text-xs font-bold text-gray-400">
                      Item level
                      <select
                        name="item_level"
                        defaultValue="0"
                        className={`${field} bg-[#090a0d] text-amber-100 [color-scheme:dark]`}
                      >
                        {Array.from(
                          { length: selected.maximum_item_level + 1 },
                          (_, level) => (
                            <option
                              key={level}
                              value={level}
                              className="bg-[#090a0d] text-amber-100"
                            >
                              +{level}
                            </option>
                          ),
                        )}
                      </select>
                    </label>
                    <label className="block text-xs font-bold text-gray-400">
                      Discount (%)
                      <input
                        name="discount_percent"
                        type="number"
                        min="0"
                        max="100"
                        defaultValue="0"
                        className={field}
                      />
                    </label>
                    <label className="block text-xs font-bold text-gray-400">
                      Description
                      <textarea name="description" rows={3} className={field} />
                    </label>
                    {selected.available_options.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-gray-400">
                          Options
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {selected.available_options.map((option) => (
                            <button
                              key={option}
                              type="button"
                              onClick={() => toggleOption(option)}
                              className={`rounded border px-2 py-1 text-[10px] ${options.includes(option) ? "border-emerald-400/50 bg-emerald-400/10 text-emerald-300" : "border-white/10 text-gray-500"}`}
                            >
                              {option}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    <label className="flex items-center gap-3 text-sm text-gray-300">
                      <input name="featured" type="checkbox" /> Featured item
                    </label>
                    <button className="w-full rounded-lg bg-amber-400 py-3 font-black text-black">
                      ADD TO SHOP
                    </button>
                  </div>
                </>
              ) : (
                <p className="mt-6 text-sm text-gray-600">
                  Select an item from the catalog.
                </p>
              )}
            </form>
          </aside>
        </div>
        <section className="mt-8 rounded-xl border border-white/10 bg-white/[.02] p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-wider text-gray-500">
                Published products
              </p>
              <h2 className="mt-1 text-xl font-black">Manage shop</h2>
            </div>
            <span className="text-xs text-gray-500">
              {products.length} products
            </span>
          </div>
          <div className="mt-4 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product) => (
              <div
                key={product.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/25 p-3"
              >
                <div className="min-w-0">
                  <strong className="block truncate text-sm text-amber-100">
                    {product.title} +
                    {String(product.selected_options.level ?? 0)}
                  </strong>
                  <span className="text-xs text-gray-500">
                    {product.price_amount.toLocaleString()}{" "}
                    {product.currency_code}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => void removeProduct(product)}
                  className="shrink-0 rounded border border-red-400/30 px-3 py-2 text-xs font-bold text-red-300 hover:bg-red-500/15"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
          {products.length === 0 && (
            <p className="mt-4 text-sm text-gray-600">No products published.</p>
          )}
        </section>
        <details className="mt-8 rounded-xl border border-white/10 bg-white/[.02] p-5">
          <summary className="cursor-pointer font-bold text-gray-300">
            Economy settings (currencies and coin packages)
          </summary>
          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <form
              onSubmit={saveCurrency}
              className="space-y-4 rounded-lg border border-white/10 p-5"
            >
              <h2 className="font-black">Add currency</h2>
              <label className="block text-xs">
                Code
                <input name="code" required className={field} />
              </label>
              <label className="block text-xs">
                Name
                <input name="name" required className={field} />
              </label>
              <label className="flex gap-2 text-sm">
                <input name="purchasable" type="checkbox" /> Purchasable
              </label>
              <button className="rounded bg-amber-400 px-5 py-2 font-black text-black">
                SAVE
              </button>
            </form>
            <form
              onSubmit={savePackage}
              className="space-y-4 rounded-lg border border-white/10 p-5"
            >
              <h2 className="font-black">Add coin package</h2>
              <label className="block text-xs">
                Title
                <input name="title" required className={field} />
              </label>
              <label className="block text-xs">
                Currency code
                <input name="currency_code" required className={field} />
              </label>
              <label className="block text-xs">
                Coins
                <input
                  name="coin_amount"
                  type="number"
                  min="1"
                  required
                  className={field}
                />
              </label>
              <label className="block text-xs">
                Bonus
                <input
                  name="bonus_amount"
                  type="number"
                  min="0"
                  defaultValue="0"
                  className={field}
                />
              </label>
              <label className="block text-xs">
                Price EUR
                <input
                  name="price"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  className={field}
                />
              </label>
              <label className="flex gap-2 text-sm">
                <input name="featured" type="checkbox" /> Featured
              </label>
              <button className="rounded bg-amber-400 px-5 py-2 font-black text-black">
                SAVE
              </button>
            </form>
          </div>
        </details>
      </div>
    </main>
  );
}
