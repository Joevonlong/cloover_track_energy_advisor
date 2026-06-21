create table if not exists plz_solar_count (
  plz        text primary key,
  count      integer not null default 0,
  seeded_at  timestamptz default now()
);

create table if not exists permit_cache (
  address_hash text primary key,
  address      text,
  result_json  jsonb,
  fetched_at   timestamptz default now()
);
