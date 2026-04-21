# Email Security (DMARC / SPF / DKIM)

This document describes the DNS records required to authenticate outbound emails
from PROBEXR and prevent spoofing.

> **IMPORTANT**: These are DNS records — they must be configured at your domain
> registrar (e.g., Cloudflare, Namecheap, GoDaddy), NOT in code.

## Prerequisites

- A custom domain configured for sending email (e.g., `probexr.com`)
- Access to your domain's DNS management panel

## Records to Add

### 1. SPF (Sender Policy Framework)

Declares which servers are authorized to send email from your domain.

| Type | Host  | Value                                                    |
|------|-------|----------------------------------------------------------|
| TXT  | `@`   | `v=spf1 include:_spf.google.com include:sendgrid.net -all` |

> Adjust `include:` entries based on your actual email provider.
> - Using **Gmail/Google Workspace**: `include:_spf.google.com`
> - Using **SendGrid**: `include:sendgrid.net`
> - Using **Amazon SES**: `include:amazonses.com`

### 2. DKIM (DomainKeys Identified Mail)

Cryptographically signs outgoing emails. Your email provider generates this.

| Type  | Host                      | Value                         |
|-------|---------------------------|-------------------------------|
| CNAME | `google._domainkey`       | *(provided by Google Workspace)* |
| CNAME | `s1._domainkey`           | *(provided by SendGrid)*      |

> Run your provider's DKIM setup wizard — they'll give you the exact record.

### 3. DMARC (Domain-based Message Authentication)

Tells receiving servers what to do when SPF/DKIM fail.

| Type | Host     | Value                                                           |
|------|----------|-----------------------------------------------------------------|
| TXT  | `_dmarc` | `v=DMARC1; p=quarantine; rua=mailto:dmarc@probexr.com; pct=100` |

**Policy options:**
- `p=none` — Monitor only (start here)
- `p=quarantine` — Mark failures as spam
- `p=reject` — Block failures entirely (strongest)

## Verification

After adding records, verify with:
- [MXToolbox](https://mxtoolbox.com/SuperTool.aspx)
- [Google Admin Toolbox](https://toolbox.googleapps.com/apps/checkmx/)
- `dig TXT _dmarc.probexr.com`
- `dig TXT probexr.com` (for SPF)

## Timeline

1. **Week 1**: Add SPF + DKIM → verify delivery
2. **Week 2**: Add DMARC with `p=none` → monitor reports
3. **Week 4**: Upgrade DMARC to `p=quarantine`
4. **Month 2+**: Upgrade to `p=reject` once confident
