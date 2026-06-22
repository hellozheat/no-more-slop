# zheat-landing structural slop (fixture notes)

Real AI-generated landing (Lovable/shadcn). Regex slop alone **PASSes**; structural scan **FAILs**.

## Expected scores (approx)

| Scan | Before cleanup |
|------|----------------|
| Slop only | ~6/35 PASS |
| Structural | ~80+/35 FAIL |
| Overall | FAIL |

## Structural hits

- `motion-copy-paste` — 20+ `shouldReduceMotion()` calls
- `motion-guard-copy-paste` — `reducedMotion ? {} :` everywhere
- `section-factory` — 11× `SectionHeader`
- `file-size-outlier` — `Portfolio.tsx` ~613 LOC
- `dead-export` — `fadeInLeft`, `cardHover`, etc. in `animations.ts`
- `duplicate-easing` — inline copy of shared easing in `HowItWorks.tsx`
- `inline-schema-org` — JSON-LD in `Index.tsx`

## What nomoreslop should do

1. Report **both** scores; never "clean" on slop PASS alone
2. Calibrate motion → extract `AnimatedSection`, use `getAnimationVariants`
3. Move schema to `lib/seo.ts`, portfolio data to `lib/portfolio.ts`
4. Delete unused animation exports
5. Do **not** touch `components/ui/` (vendor)
