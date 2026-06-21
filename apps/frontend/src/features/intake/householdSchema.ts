// Validation schema for the intake form. Mirrors the frozen `Household` contract
// in src/lib/types.ts (F02) — field names, enums and optional-ness must match.
//
// Inputs are HTML strings; required number fields coerce, and empty strings are
// normalised to `undefined` first so a blank field reads as "missing" (a clear
// required error) rather than coercing to 0.
import { z } from "zod";

const CURRENT_YEAR = 2026;

/** "" / null / undefined → undefined; everything else passes through to coerce. */
const blankToUndefined = (value: unknown) =>
  value === "" || value === null || value === undefined ? undefined : value;

function requiredNumber(opts: { min: number; max: number; int?: boolean; message: string }) {
  let schema = z.coerce.number({
    required_error: opts.message,
    invalid_type_error: opts.message,
  });
  if (opts.int) schema = schema.int(opts.message);
  return z.preprocess(blankToUndefined, schema.min(opts.min, opts.message).max(opts.max, opts.message));
}

function optionalNumber(opts: { min: number; max: number; int?: boolean; message: string }) {
  let schema = z.coerce.number({ invalid_type_error: opts.message });
  if (opts.int) schema = schema.int(opts.message);
  return z.preprocess(
    blankToUndefined,
    schema.min(opts.min, opts.message).max(opts.max, opts.message).optional(),
  );
}

export const householdSchema = z
  .object({
    address: z.object({
      street: z.string().trim().min(1, "Street is required"),
      house_no: z.string().trim().min(1, "No. is required"),
      city: z.string().trim().min(1, "City is required"),
    }),
    plz: z
      .string()
      .trim()
      .regex(/^\d{5}$/, "5-digit postal code"),
    floor_area_m2: requiredNumber({ min: 10, max: 2000, message: "Living area in m²" }),
    building_year: requiredNumber({
      min: 1850,
      max: CURRENT_YEAR,
      int: true,
      message: `Build year (1850-${CURRENT_YEAR})`,
    }),
    occupants: requiredNumber({ min: 1, max: 20, int: true, message: "People (1-20)" }),
    electricity_eur_month: requiredNumber({
      min: 1,
      max: 2000,
      message: "Electricity cost EUR/month",
    }),
    heating: z.object({
      fuel: z.enum(["OIL", "GAS"], { required_error: "Choose fuel" }),
      eur_month: requiredNumber({ min: 1, max: 3000, message: "Heating cost EUR/month" }),
    }),
    mobility: z.object({
      kind: z.enum(["PETROL", "DIESEL", "EV", "NONE"]),
      km_month: optionalNumber({ min: 0, max: 20000, message: "km/month" }),
      eur_month: optionalNumber({ min: 0, max: 3000, message: "EUR/month" }),
    }),
    // Existing equipment — optional. UI added in Phase 4; kept here so the form
    // shape and the emitted Household object stay aligned with the contract.
    existing_pv_kwp: optionalNumber({ min: 0, max: 100, message: "kWp" }),
    existing_battery_kwh: optionalNumber({ min: 0, max: 100, message: "kWh" }),
    existing_heatpump_year: optionalNumber({
      min: 1980,
      max: CURRENT_YEAR,
      int: true,
      message: `Year (1980-${CURRENT_YEAR})`,
    }),
    existing_heatpump_power_kw: optionalNumber({ min: 0, max: 100, message: "kW" }),
    existing_heatpump_scop: optionalNumber({ min: 1, max: 8, message: "SCOP (1–8)" }),
    existing_ev: z.boolean().optional(),
    existing_ev_charger: z.boolean().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.mobility.kind !== "NONE") {
      const hasKm = typeof data.mobility.km_month === "number" && data.mobility.km_month > 0;
      const hasEur = typeof data.mobility.eur_month === "number" && data.mobility.eur_month > 0;
      if (!hasKm && !hasEur) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["mobility", "km_month"],
          message: "Enter km/month or EUR/month",
        });
      }
    }
  });

/** What the form fields hold while editing (number fields are strings). */
export interface HouseholdFormInput {
  address: { street: string; house_no: string; city: string };
  plz: string;
  floor_area_m2: string;
  building_year: string;
  occupants: string;
  electricity_eur_month: string;
  heating: { fuel: "OIL" | "GAS"; eur_month: string };
  mobility: { kind: "PETROL" | "DIESEL" | "EV" | "NONE"; km_month: string; eur_month: string };
  existing_pv_kwp: string;
  existing_battery_kwh: string;
  existing_heatpump_year: string;
  existing_heatpump_power_kw: string;
  existing_heatpump_scop: string;
  existing_ev: boolean;
  existing_ev_charger: boolean;
}

/** Parsed, coerced output handed to onSubmit — structurally a `Household`. */
export type HouseholdFormOutput = z.infer<typeof householdSchema>;
