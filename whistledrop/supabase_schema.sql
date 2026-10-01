create extension if not exists pgcrypto;

create type report_category as enum ('SECURITY', 'HARASSMENT', 'CORRUPTION', 'TECHNICAL', 'OTHER');
create type report_status as enum ('SUBMITTED', 'UNDER_REVIEW', 'RESOLVED', 'DISMISSED');

create table moderators (
    id uuid primary key default gen_random_uuid(),
    username text unique not null,
    hashed_password text not null,
    created_at timestamptz not null default now()
);

create table reports (
    id uuid primary key default gen_random_uuid(),
    case_code_hash text unique not null,
    category report_category not null,
    description text not null,
    evidence_url text,
    status report_status not null default 'SUBMITTED',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_reports_case_code_hash on reports (case_code_hash);
create index idx_reports_status on reports (status);
create index idx_reports_category on reports (category);

create table status_updates (
    id uuid primary key default gen_random_uuid(),
    report_id uuid not null references reports (id) on delete cascade,
    status report_status not null,
    message text,
    moderator_id uuid references moderators (id),
    created_at timestamptz not null default now()
);

create index idx_status_updates_report_id on status_updates (report_id);
alter table moderators enable row level security;
alter table reports enable row level security;
alter table status_updates enable row level security;
