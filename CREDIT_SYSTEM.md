# Credit System Documentation

## Overview

This document explains the credit-based billing system for the Beverage Brands Dashboard. Credits are used to track and invoice customers for platform usage.

**Credit Value:** 1 credit = $0.10 USD

---

## Credit Calculation Methodology

Credits are assigned based on the computational cost and API usage of each operation. The system tracks the following actions:

| Action | Credits | Description |
|--------|---------|-------------|
| Research brand website | 10 | Scrape and analyze a brand's website for information |
| Add new brand to database | 5 | Store a new brand record in the database |
| Monthly brand update check | 2 per brand | Update existing brand metrics (per brand, per month) |
| Weekly new brand discovery | 20 per run | Automated scan for new beverage brands |
| API call (TikTok/Instagram) | 1 per call | External API calls for social media data |

---

## Credit Cost Breakdown

| Action | Credits | Our Cost | Calculation |
|--------|---------|----------|-------------|
| Research brand website | 10 | $0.50 | Scraping time + processing |
| Add brand to DB | 5 | $0.10 | Storage + indexing |
| Monthly update (per brand) | 2 | $0.05 | API costs + compute |
| Weekly discovery | 20 | $1.00 | Compute resources for scanning |
| API call (TikTok/IG) | 1 | $0.01 | RapidAPI fees |

---

## Example Monthly Usage

### Small Customer (50 brands)
- 50 brands × monthly update = 100 credits
- 5 new brands researched = 50 credits
- 4 weekly discoveries = 80 credits
- 200 API calls = 200 credits
- **Total: 430 credits = $43.00 cost**

### Medium Customer (150 brands)
- 150 brands × monthly update = 300 credits
- 10 new brands researched = 100 credits
- 4 weekly discoveries = 80 credits
- 500 API calls = 500 credits
- **Total: 980 credits = $98.00 cost**

### Large Customer (500 brands)
- 500 brands × monthly update = 1,000 credits
- 25 new brands researched = 250 credits
- 4 weekly discoveries = 80 credits
- 1,500 API calls = 1,500 credits
- **Total: 2,830 credits = $283.00 cost**

---

## Pricing Tiers for Customers

### Starter Plan
- **Credits:** 500/month
- **Price:** $75/month
- **Best for:** Small businesses, up to 50 brands
- **Per credit:** $0.15

### Professional Plan
- **Credits:** 1,500/month
- **Price:** $195/month
- **Best for:** Medium businesses, up to 150 brands
- **Per credit:** $0.13

### Enterprise Plan
- **Credits:** 5,000/month
- **Price:** $550/month
- **Best for:** Large businesses, up to 500 brands
- **Per credit:** $0.11

### Custom Plan
- **Credits:** Pay-as-you-go
- **Price:** $0.10 per credit (minimum $50/month)
- **Best for:** Variable usage or large volumes

---

## Invoice Calculation Example

**Customer:** ACME Beverages  
**Plan:** Professional Plan  
**Billing Period:** January 2024

### Usage Breakdown
| Item | Quantity | Credits | Cost |
|------|----------|---------|------|
| Monthly plan (base) | 1 | 1,500 | $195.00 |
| Additional credits used | 230 | 230 | $29.90 |
| **Total** | | **1,730** | **$224.90** |

### Calculation
- Base plan: $195.00 (includes 1,500 credits)
- Overage: 230 credits × $0.13 = $29.90
- **Total Invoice: $224.90**

---

## Credit Tracking

The system tracks credits in real-time:

1. **Dashboard Display:** Shows "X of Y credits used" with visual progress bar
2. **Color Coding:**
   - 🟢 Green: < 50% usage
   - 🟡 Yellow: 50-80% usage
   - 🔴 Red: > 80% usage

3. **Alerts:** Automatic notifications at 75% and 90% usage

---

## Internal Cost Tracking

For internal accounting, we track actual costs:

| Cost Category | Monthly Estimate |
|---------------|------------------|
| RapidAPI (TikTok/Instagram) | ~$50-200 |
| Server/Compute | ~$100-300 |
| Database hosting | ~$20-50 |
| **Total Operating Cost** | **~$170-550/month** |

---

## Notes for Nick's Presentation

- Simple credit system makes invoicing transparent
- Customers understand exactly what they're paying for
- Easy to upgrade/downgrade plans
- Overage billing at plan rate (not penalty rate)
- Credit rollover available for annual plans
