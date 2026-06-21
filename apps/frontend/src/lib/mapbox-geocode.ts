// Mapbox forward geocoding for the address autocomplete. Uses the same
// VITE_MAPBOX_TOKEN the globe already needs. Restricted to German addresses.
//
// A Mapbox "address" feature splits as: text = street, address = house number,
// center = [lon, lat], context = [{ id: "postcode…", text }, { id: "place…", text }].
const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

const ENDPOINT = "https://api.mapbox.com/geocoding/v5/mapbox.places";

export interface AddressSuggestion {
  id: string;
  /** Full human-readable place name for the dropdown row. */
  label: string;
  street: string;
  house_no: string;
  city: string;
  plz: string;
  lat: number;
  lon: number;
}

interface MapboxContext {
  id?: string;
  text?: string;
}

interface MapboxFeature {
  id?: string | number;
  place_name?: string;
  text?: string;
  address?: string;
  center?: [number, number];
  context?: MapboxContext[];
}

interface MapboxGeocodeResponse {
  features?: MapboxFeature[];
}

function contextText(context: MapboxContext[], prefix: string): string {
  const match = context.find((entry) => typeof entry.id === "string" && entry.id.startsWith(prefix));
  return match?.text ?? "";
}

/**
 * Forward-geocode a free-text address query to German address suggestions.
 * Returns [] when the token is missing or the query is too short — the caller
 * just shows no dropdown. Throws only on a non-OK HTTP response (network/abort
 * surface as the usual fetch errors for the caller to swallow).
 */
export async function geocodeAddress(
  query: string,
  signal?: AbortSignal,
): Promise<AddressSuggestion[]> {
  const trimmed = query.trim();
  if (!TOKEN || trimmed.length < 3) {
    return [];
  }

  const params = new URLSearchParams({
    access_token: TOKEN,
    country: "de",
    types: "address",
    autocomplete: "true",
    language: "de",
    limit: "1",
  });
  const url = `${ENDPOINT}/${encodeURIComponent(trimmed)}.json?${params.toString()}`;

  const res = await fetch(url, { signal });
  if (!res.ok) {
    throw new Error(`geocode ${res.status}`);
  }

  const data = (await res.json()) as MapboxGeocodeResponse;
  const features = data.features ?? [];

  return features
    .map((feature): AddressSuggestion => {
      const context = Array.isArray(feature.context) ? feature.context : [];
      return {
        id: String(feature.id ?? feature.place_name ?? Math.random()),
        label: feature.place_name ?? "",
        street: feature.text ?? "",
        house_no: feature.address ?? "",
        city: contextText(context, "place") || contextText(context, "locality"),
        plz: contextText(context, "postcode"),
        lat: Number(feature.center?.[1]),
        lon: Number(feature.center?.[0]),
      };
    })
    .filter((suggestion) => Number.isFinite(suggestion.lat) && Number.isFinite(suggestion.lon));
}
