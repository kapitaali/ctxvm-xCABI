# RR-20261101 — npm scope mechanics PINNED; one naming-card finding corrected

**Card:** the `UNVERIFIED-2026-11-01` gates registered by
`reports/RR-NAMING-20261101.md` (the scoped-namespace mechanics quote) and
present on the W10 board since 2026-10-29 ("npm scope `@ctxvm` UNVERIFIED,
org page 403"). Three npm documentation pages were fetched directly (the
web-search tool was down, but docs.npmjs.com serves content to a plain
fetch). **Result: the mechanics are now pinned verbatim — and one finding of
the naming card is CORRECTED below (append-only; the naming card text is not
edited).** Date: 2026-11-01.

## 1. The pinned quotes (locators + page edit dates from each footer)

- `https://docs.npmjs.com/about-scopes` (footer: "Last edited … on October 23,
  2023"):
  > "When you sign up for an npm user account or create an organization, you
  > are granted a scope that matches your user or organization name. You can
  > use this scope as a namespace for related packages."
  > "A scope allows you to create a package with the same name as a package
  > created by another user or organization without conflict."
- `https://docs.npmjs.com/creating-and-publishing-scoped-public-packages`
  (footer: "Last edited … on September 29, 2026"):
  - "Before you can publish user-scoped npm packages, you must sign up for an
    npm user account. Additionally, to publish organization-scoped packages,
    you must create an npm user account, then create an npm organization."
  - "By default, scoped packages are published with private visibility. To
    publish a scoped package with public visibility, use
    `npm publish --access public`."
- `https://docs.npmjs.com/creating-an-organization` (footer: "Last edited …
  on August 18, 2025"):
  - "Your organization name will also be your organization scope."
  - The creation flow offers "either the 'Unlimited private packages' paid
    plan or the 'Unlimited public packages' free plan" — **creating the org
    itself is free under the public-packages plan.**

## 2. THE CORRECTION (supersedes one sentence of RR-NAMING-20261101)

RR-NAMING-20261101 fact 3 read: "**the scope belongs to the first publish
under it** … if publish-time is ever reached, the first publish under
`@ctxvm` should happen promptly to claim the namespace."

Per the pinned quotes, that is **wrong in detail**: a scope name is not
claimed by any party on publish — it is **granted when the npm user account
or organization with that name is created** (both unique across npm). The
correct mechanics:

1. The `@ctxvm` scope exists when an account (user) or organization named
   `ctxvm` is created — for an org, that is a **free** plan action and it can
   precede any publish by an arbitrary time.
2. Publishing inside an existing scope is package-additive and does not
   change namespace ownership (any member of the org publishes; ownership
   lives at the org).
3. Scoped publishes are **private by default** and must pass
   `npm publish --access public` to be visible — a publish-time mechanics
   fact W10/D6 should carry when the node package is ever shipped.

The publication-ordering implication is therefore **refined, not reversed**:
the D6-relevant claim act is "create the npm org/user named `ctxvm`
promptly", not "publish promptly"; the naming card's numbered finding keeps
its availability verdict (scoped availability NOT decidable pre-publish
without creating the account) and loses nothing else.

## 3. What was NOT performed

- No account or organization was created, renamed, or reserved anywhere
  (user-gated by definition; the naming card's discipline continues).
- The availability of the *signup name* `ctxvm` (user or org) remains
  uncheckable without an owner-side account interaction — the 2026-10-29
  observe-the-org-page-403 note stands; nothing today makes that decidable
  anonymously.
- Web/domain collision pass: still UNVERIFIED-2026-11-01 (unchanged from
  RR-NAMING; the search integration is down this session).

## 4. Bookkeeping in this card

- The LOG gains one row (supersession recorded there, since LOG rows are
  append-only and cannot be edited).
- The HANDOFF gains an append-only §0 block with the same correction so the
  active record does not rely on remembering the LOG tail.
- The W10 board row is NOT edited: its standing text ("npm scope `@ctxvm`
  UNVERIFIED (org page 403)") remains exactly true.

## 5. Deviations

None. Three read-only doc fetches; two of them returned page content with
commit-linked edit dates recorded above. No code, schema, corpus, or
package-metadata change. No registry write anywhere.
