# Privacy Policy — PROBEXR

**Last Updated:** April 21, 2026  
**Effective Date:** April 21, 2026

---

## 1. Introduction

PROBEXR ("we", "us", "our") operates the PROBEXR web application at [https://probexr.vercel.app](https://probexr.vercel.app) (the "Service"). This Privacy Policy explains how we collect, use, store, and protect your personal data when you use our Service.

By using PROBEXR, you agree to the practices described in this policy.

---

## 2. Data We Collect

### 2.1 Account Data
When you create an account, we collect:
- **Email address** — used for authentication, verification, and account recovery.
- **Full name** (optional) — provided by you or imported from a social login provider.
- **Avatar URL** (optional) — imported from Google or GitHub if you use social login.
- **Password hash** — we never store your plaintext password. Passwords are hashed using Argon2id, a modern, secure hashing algorithm.

### 2.2 Social Login Data
If you sign in via Google or GitHub, we receive:
- Your **email**, **name**, **profile picture**, and **provider-specific user ID**.
- We do **not** receive or store your social account password.

### 2.3 Content Data
When you use the Service, we process and store:
- **Text you paste** for summarization.
- **URLs you submit** for article ingestion (the fetched and cleaned content is stored).
- **Summaries** generated from your content.
- **Chat messages** exchanged with the document chat feature.
- **Flashcards** generated from your documents.
- **Synthesis results** from multi-document analysis.

### 2.4 Usage & Analytics Data
We collect aggregated, non-identifying usage statistics:
- Summarization count, word counts, and feature usage frequency.
- These are used to display your personal analytics dashboard and are **not shared** with third parties.

### 2.5 Technical Data
We automatically collect:
- **IP address** — used for rate limiting and abuse prevention. IP addresses are not stored persistently; they are used transiently in rate-limit keys that expire within 60 seconds.
- **Request metadata** — HTTP method, path, status code, and response time are logged for operational monitoring. Logs are retained for up to 30 days.
- **Request ID** — a random correlation ID for debugging, with no personal data.

---

## 3. Third-Party Data Processing

### 3.1 LLM Providers
When you use AI-powered summarization, chat, synthesis, or flashcard generation, your submitted text is sent to a third-party Large Language Model (LLM) provider for processing. The specific provider depends on our server configuration and may include:

- **Groq** ([Privacy Policy](https://groq.com/privacy-policy/))
- **OpenAI** ([Privacy Policy](https://openai.com/policies/privacy-policy))
- **OpenRouter** ([Privacy Policy](https://openrouter.ai/privacy))

> **Important:** Your content is transmitted to these providers for processing only. We do not control how these providers handle your data beyond the terms of their respective APIs. We recommend reviewing their privacy policies if you have concerns about sensitive content.

**What we send:** The text you submit (article content, chat messages, synthesis prompts).  
**What we do NOT send:** Your email, password, account information, or any personal identifiers.

### 3.2 Extractive Mode
If no LLM provider is configured, summarization uses a fully local, extractive algorithm. **No data leaves our servers** in this mode.

### 3.3 Email Provider
If SMTP is configured, transactional emails (verification, password reset, magic links) are sent through our configured SMTP provider (e.g., SendGrid, Amazon SES, or Resend). Only the recipient email address and email content are shared.

### 3.4 Hosting Providers
- **Frontend:** Hosted on Vercel (subject to [Vercel's Privacy Policy](https://vercel.com/legal/privacy-policy)).
- **Backend:** Hosted on Render (subject to [Render's Privacy Policy](https://render.com/privacy)).

---

## 4. How We Use Your Data

We use your data to:
- **Provide the Service** — process your text, generate summaries, and power features.
- **Authenticate you** — verify your identity via email/password, social login, or magic links.
- **Protect the Service** — rate limiting, CSRF protection, account lockout, and abuse prevention.
- **Improve the Service** — aggregated, anonymized analytics to understand usage patterns.
- **Communicate with you** — send verification emails, password reset links, and magic login links.

We do **not**:
- Sell your data to third parties.
- Use your content for advertising.
- Train AI models on your data.
- Share your personal information with third parties except as described in Section 3.

---

## 5. Data Storage & Retention

### 5.1 Database
Your account and content data is stored in a PostgreSQL database hosted by our backend provider. Data is encrypted in transit (TLS) and at rest (provider-managed encryption).

### 5.2 Cache
Summary results are cached in Redis for up to 24 hours to improve performance. Cache entries are keyed by a SHA-256 hash of your content — no personal identifiers are used as cache keys.

### 5.3 Retention Periods
| Data Type | Retention |
|-----------|-----------|
| Account data | Until you delete your account |
| Documents & summaries | Until you delete them (soft-delete, then permanent after 90 days) |
| Chat sessions | Until the associated document is deleted |
| Refresh tokens | Automatically purged hourly after expiration or revocation |
| Rate-limit data | 60 seconds (Redis TTL) |
| Application logs | Up to 30 days |
| Cache entries | Up to 24 hours |

---

## 6. Data Security

We implement industry-standard security measures:
- **Argon2id** password hashing.
- **JWT tokens** in HttpOnly, Secure, SameSite cookies.
- **CSRF protection** via dual-submit cookie pattern with timing-safe comparison.
- **Rate limiting** on all endpoints (IP, per-user, and per-email tiers).
- **Account lockout** after repeated failed login attempts.
- **SSRF protection** on URL ingestion with private IP blocklisting.
- **Prompt injection sanitization** on all user content before LLM processing.
- **Content Security Policy**, **HSTS**, **X-Frame-Options**, and other security headers.
- **Non-root Docker container** with minimal attack surface.

---

## 7. Your Rights

You have the right to:
- **Access** your data — view your profile, documents, and analytics via the Service.
- **Correct** your data — update your profile information at any time.
- **Delete** your data — delete individual documents, or request full account deletion by contacting us.
- **Export** your data — export flashcards as CSV. Additional export formats may be added in the future.
- **Withdraw consent** — stop using the Service at any time. Deleting your account removes all associated data.

### For EU/EEA Users (GDPR)
If you are located in the European Union or European Economic Area, you additionally have the right to:
- **Data portability** — request a machine-readable copy of your data.
- **Restriction of processing** — request that we limit how we use your data.
- **Object to processing** — object to processing based on legitimate interests.
- **Lodge a complaint** — with your local data protection authority.

---

## 8. Cookies

PROBEXR uses the following cookies:

| Cookie | Purpose | HttpOnly | Duration |
|--------|---------|----------|----------|
| `access_token` | Authentication (JWT) | ✅ Yes | 15 minutes |
| `refresh_token` | Session renewal | ✅ Yes | 7 days |
| `csrf_token` | CSRF protection | ❌ No (JS-readable) | 24 hours |
| `oauth_state` | OAuth CSRF prevention | ✅ Yes | 10 minutes |

All cookies are **functional** — they are necessary for the Service to operate. We do not use advertising or analytics cookies.

---

## 9. Children's Privacy

PROBEXR is not intended for children under 13 years of age. We do not knowingly collect personal data from children. If you believe a child has provided us with personal data, please contact us and we will delete it.

---

## 10. Changes to This Policy

We may update this Privacy Policy from time to time. When we make material changes, we will update the "Last Updated" date at the top of this document. Continued use of the Service after changes constitutes acceptance of the updated policy.

---

## 11. Contact

If you have questions about this Privacy Policy, your data, or wish to exercise your rights, please contact:

**Email:** privacy@probexr.com  
**GitHub:** [github.com/amankrrishav/PROBEXR](https://github.com/amankrrishav/PROBEXR)
