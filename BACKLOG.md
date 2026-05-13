# PROBEXR — Deferred Backlog (P3)

> Items identified during the 2026-05-14 production audit that are **not yet implemented**.
> Revisit these when scaling, onboarding enterprise users, or expanding to new regions.

---

## Security

| # | Item | When to do | Effort | Notes |
|---|------|-----------|--------|-------|
| 17 | **Webhook signature verification** | When webhooks are added | Medium | No webhooks exist yet — nothing to sign |
| 18 | **SRI for CDN-loaded fonts** | If self-hosting fonts | Low | Not feasible with Google Fonts / Fontshare (dynamic CSS per User-Agent) |
| 19 | **WAF integration** (Cloudflare/AWS WAF) | Before launch marketing | Medium | Requires Cloudflare or AWS account setup |
| 20 | **DMARC/SPF/DKIM for SMTP** | Before enabling production email | Medium | Requires DNS TXT records on your domain registrar |
| 21 | **Secrets rotation automation** | At scale / enterprise | High | Needs HashiCorp Vault or AWS Secrets Manager |

## Operations

| # | Item | When to do | Effort | Notes |
|---|------|-----------|--------|-------|
| 22 | **Database backup automation** | Immediately after launch | Medium | Configure via Render/Supabase/AWS RDS automated backups |
| 23 | **Staging environment** | Before adding team members | Medium | Clone Render service with `ENVIRONMENT=staging` |
| 24 | **Blue-green / canary deploys** | At scale (>1000 DAU) | High | Requires load balancer config (Render doesn't natively support) |
| 25 | **Centralized log aggregation** (Loki/ELK) | When debugging production issues | High | Sentry covers errors; full log aggregation is a separate project |
| 26 | **Uptime monitoring** | Immediately after launch | **5 min** | Sign up for [UptimeRobot](https://uptimerobot.com) free tier, add `https://your-domain/api/v1/health` |
| 27 | ~~LLM API cost tracking~~ | ✅ **Done** (2026-05-14) | — | — |

## Testing

| # | Item | When to do | Effort | Notes |
|---|------|-----------|--------|-------|
| 28 | **Contract tests** (frontend ↔ backend) | When API is versioned | Medium | 450 integration tests already cover the API surface |
| 29 | **Visual regression tests** | Before major UI redesign | High | Needs Playwright + screenshot comparison setup |
| 30 | **Chaos engineering** (Redis down, DB slow) | At scale | High | Needs infrastructure to simulate failures |

## Architecture

| # | Item | When to do | Effort | Notes |
|---|------|-----------|--------|-------|
| 31 | **Internationalization (i18n)** | When targeting non-English markets | Very High | Affects every UI string; use `react-intl` or `i18next` |
| 32 | ~~Accessibility audit (WCAG 2.1 AA)~~ | ✅ **Done** (2026-05-14) | — | — |

## Compliance

| # | Item | When to do | Effort | Notes |
|---|------|-----------|--------|-------|
| 33 | ~~SBOM generation~~ | ✅ **Done** (2026-05-14) | — | CI step via `pip-licenses` |

---

## Quick wins to do first after launch

1. **#26 Uptime monitoring** — literally 5 minutes on UptimeRobot free tier
2. **#22 Database backups** — enable in your cloud provider dashboard
3. **#23 Staging environment** — clone your Render service

## Requires DNS / domain access

- **#20 DMARC/SPF/DKIM** — add TXT records for your SMTP domain

## Requires cloud provider accounts

- **#19 WAF** — Cloudflare free tier provides basic WAF
- **#25 Log aggregation** — Grafana Cloud free tier (50GB logs/month)

---

*Last updated: 2026-05-14. Generated from production audit Report.md.*
