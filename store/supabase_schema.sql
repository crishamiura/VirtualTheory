-- =====================================================================
-- Vital Theory store — Supabase (Postgres) schema
-- Run this ONCE in your Supabase project: Dashboard > SQL Editor > New query
-- (paste this whole file, then "Run"). It creates the orders table the store
-- reads/writes through PostgREST.
-- =====================================================================

create table if not exists public.orders (
  id          bigint generated always as identity primary key,
  order_no    text unique,
  name        text,
  email       text,
  country     text,
  product     text,
  amount      numeric,
  currency    text,
  status      text default 'pending',
  method      text,
  token       text unique,
  ref         text,          -- external reference (e.g. Gumroad sale_id / Stripe session)
  created_at  timestamptz default now(),
  paid_at     timestamptz
);

create index if not exists orders_token_idx on public.orders (token);
create index if not exists orders_ref_idx   on public.orders (ref);

-- Row Level Security on. Orders contain customer emails (PII), so keep this ON.
alter table public.orders enable row level security;

-- RECOMMENDED: run the store backend with your SERVICE ROLE key
-- (Dashboard > Project Settings > API > service_role). It bypasses RLS, so no
-- public policy is needed and the publishable/anon key can never read orders.
-- Put that key in store/.env as SUPABASE_KEY.

-- ALTERNATIVE (less secure): if you must run the backend with the publishable
-- (anon) key you gave, uncomment the policy below so it can read/write. Only do
-- this if that key stays server-side and is never shipped to a browser, because
-- anyone with the anon key could then read every order.
--
-- create policy "server anon full access" on public.orders
--   for all to anon using (true) with check (true);


-- =====================================================================
-- Keep-alive table — used by the Vercel cron (api/keepalive.py) to stop
-- the free-tier project from auto-pausing. Holds only a timestamp, so it
-- is safe to allow the publishable (anon) key to update it.
-- =====================================================================
create table if not exists public.keepalive (
  id        int primary key default 1,
  last_ping timestamptz default now()
);
insert into public.keepalive (id) values (1) on conflict (id) do nothing;

alter table public.keepalive enable row level security;

create policy "keepalive update (anon)" on public.keepalive
  for all to anon using (true) with check (true);
