"use client";
/* eslint-disable @next/next/no-img-element */

import { useEffect, useState } from "react";
import PageScaffold from "@/components/PageScaffold";
import {
  getCommerceCatalog,
  getGameItemImageUrl,
  searchGameItems,
  type CommerceCatalog,
  type GameItemCatalogItem,
  type ShopProduct,
} from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";

function activeDiscount(item: ShopProduct) {
  const now = Date.now();
  const starts = item.discount_starts_at
    ? new Date(item.discount_starts_at).getTime()
    : 0;
  const ends = item.discount_ends_at
    ? new Date(item.discount_ends_at).getTime()
    : Number.MAX_SAFE_INTEGER;
  return item.discount_percent > 0 && now >= starts && now < ends;
}
function powerValue(
  power: GameItemCatalogItem["base_power_ups"][number],
  level: number,
) {
  return (
    power.base_value +
    (power.level_bonuses.find((bonus) => bonus.level === level)?.value ?? 0)
  );
}
function powerDisplay(attribute: string, value: number) {
  if (attribute === "Attack Damage Increase Multiplier")
    return [`Damage increase`, `+${Math.round((value - 1) * 100)}%`];
  if (attribute === "Damage Receive Multiplier")
    return ["Damage absorption", `${Math.round((1 - value) * 100)}%`];
  return [
    attribute,
    Number.isInteger(value) ? String(value) : value.toFixed(2),
  ];
}
const INVENTORY_SLOT_SIZE = 32;

function inventoryItemSize(
  item?: Pick<GameItemCatalogItem, "width" | "height">,
) {
  return {
    width: Math.max(1, item?.width ?? 1) * INVENTORY_SLOT_SIZE,
    height: Math.max(1, item?.height ?? 1) * INVENTORY_SLOT_SIZE,
  };
}

function inventoryItemImageSize(
  item: Pick<GameItemCatalogItem, "width" | "height">,
) {
  const longestSide = Math.max(1, item.width, item.height);
  const size = longestSide * INVENTORY_SLOT_SIZE;
  return { width: size, height: size };
}
function ProductCard({
  item,
  gameItem,
}: {
  item: ShopProduct;
  gameItem?: GameItemCatalogItem;
}) {
  const discounted = activeDiscount(item);
  const price = discounted
    ? Math.round((item.price_amount * (100 - item.discount_percent)) / 100)
    : item.price_amount;
  const options = Array.isArray(item.selected_options.options)
    ? item.selected_options.options
    : [];
  const level = Number(item.selected_options.level ?? 0);
  const powers =
    gameItem?.base_power_ups.map((power) =>
      powerDisplay(power.attribute, powerValue(power, level)),
    ) ?? [];
  const variant = options.some((option) =>
    option.toLowerCase().includes("ancient"),
  )
    ? "ancient"
    : options.some((option) => option.toLowerCase().includes("excellent"))
      ? "excellent"
      : "normal";
  return (
    <article className="group relative flex h-full flex-col rounded-xl border border-amber-300/15 bg-[linear-gradient(145deg,#15120e,#090a0d_65%)] p-3 shadow-xl shadow-black/30 transition hover:z-40 hover:-translate-y-1 hover:border-amber-300/40">
      <div className="flex h-40 w-full items-center justify-center">
        {gameItem ? (
          <div
            className="shop-inventory-item relative flex shrink-0 items-center justify-center overflow-hidden"
            style={inventoryItemSize(gameItem)}
          >
            <img
              src={getGameItemImageUrl(gameItem, level, variant)}
              alt={item.title}
              className="max-w-none shrink-0 object-contain transition duration-500 group-hover:scale-105"
              style={inventoryItemImageSize(gameItem)}
              onError={(event) => {
                const fallback = getGameItemImageUrl(gameItem);
                if (event.currentTarget.src !== fallback) {
                  event.currentTarget.src = fallback;
                }
              }}
            />
          </div>
        ) : (
          <div
            className="shop-inventory-item flex items-center justify-center text-center"
            style={inventoryItemSize()}
          >
            <span className="text-5xl text-amber-300/30">◆</span>
          </div>
        )}
      </div>
      <p className="mu-kicker mt-3">{gameItem?.category || item.category}</p>
      <h2 className="mt-1 truncate text-base font-black text-amber-100">
        {item.title} <span className="text-amber-400">+{level}</span>
      </h2>
      <p className="mt-1 line-clamp-2 min-h-9 text-xs leading-[18px] text-gray-500">
        {item.description}
      </p>
      <div className="mt-auto flex items-end justify-between border-t border-white/10 pt-3">
        <div>
          <div className="flex items-center gap-2">
            <strong className="text-base text-amber-300">
              {price.toLocaleString()} {item.currency_code}
            </strong>
            {discounted && (
              <span className="rounded bg-red-600 px-1.5 py-0.5 text-[9px] font-black text-white">
                -{item.discount_percent}%
              </span>
            )}
          </div>
          {discounted && (
            <div className="text-[10px] text-gray-600 line-through">
              {item.price_amount.toLocaleString()} {item.currency_code}
            </div>
          )}
        </div>
        <span className="text-[8px] uppercase tracking-wider text-gray-600">
          Login required
        </span>
      </div>
      <div className="shop-item-tooltip invisible absolute left-[calc(100%+12px)] top-0 z-50 w-56 rounded-lg border border-amber-300/35 bg-[#08090c] p-3 opacity-0 shadow-[0_20px_70px_rgba(0,0,0,.95)] transition group-hover:visible group-hover:opacity-100">
        <h3 className="font-black text-amber-200">
          {item.title} +{level}
        </h3>
        <p className="mt-1 text-sm font-bold text-amber-300">
          {price.toLocaleString()} {item.currency_code}
        </p>
        <table className="mt-2 w-full text-xs">
          <tbody className="divide-y divide-white/5">
            {[["Type", gameItem?.slot || item.category], ...powers.slice(0, 3)]
              .filter(([, value]) => value !== undefined && value !== null)
              .map(([label, value]) => (
                <tr key={String(label)}>
                  <th className="py-1.5 text-left font-normal text-gray-600">
                    {label}
                  </th>
                  <td className="py-1.5 text-right text-gray-300">{value}</td>
                </tr>
              ))}
          </tbody>
        </table>
        {options.length > 0 && (
          <div className="mt-2 border-t border-white/10 pt-2">
            {options.slice(0, 4).map((option) => (
              <p key={option} className="mt-1 text-[11px] text-emerald-400">
                ◆ {option}
              </p>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}

export default function ShopPage() {
  const { t } = useLanguage();
  const [data, setData] = useState<CommerceCatalog | null>(null);
  const [gameItems, setGameItems] = useState<
    Record<string, GameItemCatalogItem>
  >({});
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getCommerceCatalog(controller.signal)
      .then(async (catalog) => {
        setData(catalog);
        const linkedIds = new Set(
          catalog.products
            .map((product) => product.openmu_item_id)
            .filter((id): id is string => Boolean(id)),
        );
        const matches = linkedIds.size
          ? await searchGameItems("", controller.signal, "", 1000)
          : [];
        setGameItems(
          Object.fromEntries(
            matches
              .filter((gameItem) => linkedIds.has(gameItem.id))
              .map((gameItem) => [gameItem.id, gameItem]),
          ),
        );
      })
      .catch((reason: unknown) => {
        if (!(reason instanceof DOMException && reason.name === "AbortError"))
          setError(
            reason instanceof Error ? reason.message : "Catalog unavailable.",
          );
      });
    return () => controller.abort();
  }, []);

  const products = data?.products ?? [];
  const productCategory = (item: ShopProduct) =>
    item.openmu_item_id
      ? (gameItems[item.openmu_item_id]?.category ?? item.category)
      : item.category;
  const categories = Array.from(new Set(products.map(productCategory)))
    .filter(Boolean)
    .sort();
  const visibleProducts =
    selectedCategory === "All"
      ? products
      : products.filter((item) => productCategory(item) === selectedCategory);

  return (
    <PageScaffold
      eyebrow="ANASTARIA ARMORY"
      title={t("shop")}
      description="Real OpenMU items, grouped so you can find equipment and consumables quickly."
    >
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {["All", ...categories].map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setSelectedCategory(category)}
              className={`rounded-lg border px-4 py-2 text-xs font-bold transition ${selectedCategory === category ? "border-amber-300 bg-amber-300 text-black" : "border-white/10 bg-black/25 text-gray-400 hover:border-amber-300/40 hover:text-amber-200"}`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>
      {error && (
        <div className="mu-panel rounded-xl p-10 text-red-400">{error}</div>
      )}
      {data && products.length === 0 && (
        <div className="mu-panel rounded-xl p-10 text-gray-500">
          No active shop products have been published yet.
        </div>
      )}
      {products.length > 0 && visibleProducts.length === 0 && (
        <div className="mu-panel rounded-xl p-10 text-gray-500">
          No products in this category.
        </div>
      )}
      <section className="grid auto-rows-fr gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {visibleProducts.map((item) => (
          <ProductCard
            key={item.id}
            item={item}
            gameItem={
              item.openmu_item_id ? gameItems[item.openmu_item_id] : undefined
            }
          />
        ))}
      </section>
    </PageScaffold>
  );
}
