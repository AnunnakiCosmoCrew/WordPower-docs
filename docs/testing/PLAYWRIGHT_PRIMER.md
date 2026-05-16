# Playwright for WordPower — a practical primer

Written 2026-05-16 after the Phase 4 re-test cycle, where 4 of 11 "fixed" bugs had regressed in production and the existing test suite missed all of them. This document is the conceptual foundation you need before reading the proposed Playwright suite issues.

You don't need to read this all at once. Sections 1–4 give you the mental model in ~10 minutes. Sections 5–7 are the WordPower-specific bits and a worked example. Sections 8+ are reference material for when you start writing tests.

---

## 1. What Playwright is, in one paragraph

**Playwright is a tool that drives a real browser** (Chrome, Firefox, Safari) **from a script you write in TypeScript or JavaScript.** You write code like *"open this URL, type into this field, click this button, assert this text appeared"*, and Playwright executes those actions against a real browser instance — the same way a human user would, except scripted and repeatable. It's made by Microsoft, open-source, and is the de-facto standard for browser E2E (end-to-end) testing in 2026.

It is **not** a unit testing framework, a visual regression tool, or a load testing tool. It is specifically for *"does this user-facing flow work end to end in a real browser against a real backend"*.

---

## 2. Mental model — three layers of testing

You currently have testing at two layers:

| Layer | Example in WordPower | What it tests | Speed | Catches |
|---|---|---|---|---|
| **Unit test** | `RootFamiliesIndexTest.kt` | A single function/class in isolation | ms | Logic errors in pure code |
| **Integration test** | `WordsControllerTest.java` with MockMvc | One component + its immediate deps (HTTP layer + service + repo) | seconds | API contracts, query behavior |
| **End-to-end (E2E) test** ← Playwright | "Capture a word and verify it appears on Home" | The entire system — browser, network, backend, DB — same as a user | tens of seconds | Anything visible to the user |

Playwright is the third layer. It catches different bugs than the first two: things like *"the backend works fine but the frontend doesn't display the response correctly"*, *"the local app works but the deployed one has the wrong COOP headers"*, *"the duplicate snackbar exists but doesn't include a 'View' action"*. These are exactly the categories of bugs that have been slipping past your current gates.

Trade-off: E2E tests are **slower** (seconds vs. milliseconds), **flakier** (network, timing, real browser quirks), and **more expensive to maintain** (every UI change can break them). The discipline is to write *few* E2E tests, but make them cover the highest-value flows.

---

## 3. Anatomy of a Playwright test

Here's a complete, runnable Playwright test. Read it top-to-bottom; you'll understand every line by the end of this section even if you've never seen one before.

```typescript
// File: e2e/tests/smoke.spec.ts
import { test, expect } from '@playwright/test';

test('home page loads and shows the Add Word button', async ({ page }) => {
  await page.goto('https://wordpower-f2398.web.app');
  const addWordButton = page.getByRole('button', { name: 'Add Word' });
  await expect(addWordButton).toBeVisible();
});
```

Walking through it:

- **`import { test, expect } from '@playwright/test';`** — pulls in the two things every test needs: `test` (defines a test case) and `expect` (assertions).
- **`test('home page loads ...', async ({ page }) => {...})`** — defines one test case. The string is the human-readable name. `async ({ page }) => {...}` is the test function. `page` is the **fixture** Playwright passes in — it's an opened browser tab you can drive.
- **`await page.goto('...')`** — navigate the tab to a URL. Everything is `async`/`await` because everything involves the browser.
- **`page.getByRole('button', { name: 'Add Word' })`** — this is a **locator**. It does not click or query immediately; it's a *description* of an element. Playwright will resolve it the moment you act on it. We'll come back to locators (they're the heart of the framework).
- **`await expect(addWordButton).toBeVisible()`** — an assertion. `expect` is special in Playwright: it **retries automatically** for up to 5 seconds by default. If the button isn't visible yet because the page is still loading, Playwright waits and re-checks until it is, or fails.

That's it. That's the whole structure. Every test is:

1. Navigate / set up
2. Locate something
3. Act on it (`click`, `fill`, `press`)
4. Assert something

You'll have hundreds of these calls across a real suite, but they all follow this shape.

### Running the test

```bash
npx playwright test                  # run all tests, headless
npx playwright test smoke.spec.ts    # run one file
npx playwright test --ui             # interactive UI mode — single most valuable command
npx playwright test --debug          # step-through debugger
```

The `--ui` mode opens a window where you can see each test step, the browser state at every action, network requests, console messages, and the locator highlights. **This is where you'll spend 80% of your debugging time.** It's also the best way to learn — write a test, run it in UI mode, watch what it does, adjust.

There's also `npx playwright codegen https://wordpower-f2398.web.app`: opens a real browser, you click around in the actual app, and Playwright **writes the test code for you** as you go. It's the fastest way to start a new test from scratch.

---

## 4. Locators — the one concept that matters most

A locator answers the question *"how do I tell Playwright which element to click?"* Get this right and tests are stable for months. Get it wrong and you'll be debugging selectors forever.

Playwright has six built-in locators, in order of preference:

1. **`getByRole('button', { name: 'Save' })`** — by ARIA role + accessible name. Most stable. Survives styling changes, class renames, layout changes. **Always reach for this first.**
2. **`getByLabel('Email')`** — by the label text associated with a form field. Stable.
3. **`getByPlaceholder('Search domains...')`** — by placeholder text. Stable.
4. **`getByText('Welcome back')`** — by visible text content. OK for unique strings, bad for common ones (`getByText('Save')` could match anywhere).
5. **`getByTestId('quiz-next-button')`** — by an explicit `data-testid` attribute you add to the markup. Very stable, but requires the team to be disciplined about adding them.
6. **`locator('div.quiz-option:nth-child(2)')`** — raw CSS selector. **Avoid.** Breaks the moment anyone changes the markup.

Why does the order matter? Because options 1–3 are based on what the **user perceives** (roles, labels, placeholders), and the UI rarely changes those. Options 4–6 are based on implementation details that change every refactor.

### Putting them together

You can chain locators to narrow down:

```typescript
// "Find the dialog labelled 'Add to list', then within it find the button named 'New list'"
const newListButton = page
  .getByRole('dialog', { name: 'Add to list' })
  .getByRole('button', { name: 'New list' });

await newListButton.click();
```

This is way more durable than `page.locator('.dialog > .actions > button:last-child')`.

---

## 5. The Flutter web problem — and what `Semantics` is

This is the section that matters most for your project specifically.

### The problem

Most websites are built with HTML elements — `<button>`, `<input>`, `<div>`, `<form>`. The browser knows what these are, screen readers know what these are, and **Playwright's `getByRole` / `getByLabel` selectors work out of the box** because the elements expose their role and name to the accessibility tree.

Flutter web works differently because of a deliberate architectural choice. The framework has two renderers: an **HTML renderer** (translates widgets into real HTML elements) and **CanvasKit** (paints the entire app as pixels onto a single `<canvas>`). CanvasKit is the default on desktop browsers and it's what WordPower uses. The trade: pixel-perfect cross-platform consistency (your iOS, Android, and web builds render identically) in exchange for the app being opaque to anything that reads the DOM.

Concretely, when you open WordPower's Home in devtools, you see something like:

```html
<body>
  <flutter-view>
    <flt-glass-pane>
      <canvas width="1920" height="963"></canvas>  <!-- the entire app -->
    </flt-glass-pane>
    <flt-semantics-host></flt-semantics-host>      <!-- mostly empty by default -->
  </flutter-view>
</body>
```

Compare to what a plain-HTML version of the same screen would expose to the browser:

```html
<body>
  <h1>WordPower</h1>
  <button>Add Word</button>
  <button>Quiz</button>
  <nav>
    <a href="/lists">My Lists</a>
    ...
  </nav>
  <ul>
    <li>tachycardia</li>
    <li>obsequious</li>
  </ul>
</body>
```

The first version is what Flutter produces. The second is what Playwright (and most other web tooling) was designed to operate on. **There is no `<button>` element for "Add Word" in the Flutter version** — it's a region of pixels on the canvas.

This single decision cascades into everything that depends on a structured DOM:

- **Cmd+F doesn't find on-screen text.** Open the app, search for "obsequious" — nothing matches, even though the word is plainly visible.
- **Right-click → Inspect always points at the canvas.** You can't inspect a chip or a label individually.
- **Screen readers see nothing by default.** Blind users hit a wall unless the developer publishes accessibility info.
- **Browser extensions are blind.** Password managers, translators, ad blockers — all empty-handed.
- **SEO is dead.** Search crawlers see "an app loaded here" and nothing else.
- **Automation tools see nothing.** This is the Playwright problem.

You saw the symptom directly in my smoke testing: `find('Add Word button')` returned *"No elements found in the accessibility tree"* and I fell back to clicking pixel coordinates like `(782, 322)`. The coordinates change with every layout tweak, which is why coordinate-based tests are unmaintainable as a strategy.

This isn't a bug Flutter will eventually fix — it's the architectural shape of the framework, and the team made the trade deliberately to win pixel-perfect cross-platform rendering. The fix is the side-channel below.

### The fix: `Semantics`

Flutter ships a built-in widget called `Semantics` that **publishes accessibility metadata into the DOM**, even when the actual rendering happens on canvas. When you wrap a widget in `Semantics(label: 'Save word')`, Flutter adds a hidden DOM node (inside that `<flt-semantics-host>` region above) with `role="button"` and `aria-label="Save word"` — real HTML that screen readers and Playwright can find. The user sees no visual change; the DOM gets a parallel accessibility tree that bridges back to the web-native world.

Here's what it looks like in code:

```dart
// BEFORE — bare TextField. Playwright can't address it by role or label.
TextField(
  controller: _wordController,
  decoration: const InputDecoration(labelText: 'Word'),
  onSubmitted: (_) => _save(),
)
```

```dart
// AFTER — wrapped in Semantics with an explicit label.
Semantics(
  label: 'Word input',
  textField: true,
  child: TextField(
    controller: _wordController,
    decoration: const InputDecoration(labelText: 'Word'),
    onSubmitted: (_) => _save(),
  ),
)
```

With the `Semantics` wrapper, Playwright can now reliably find the field:

```typescript
const wordInput = page.getByLabel('Word input');
await wordInput.fill('obsequious');
await page.keyboard.press('Enter');
```

No coordinate hacks. No brittle CSS selectors. The test works regardless of how the visual layout changes.

### What needs annotating

Not every widget — just the ones tests will interact with. For WordPower the rough list is:

- **Quick Capture:** the word input, the notes toggle, the notes field, the Save button
- **Word detail:** the title, the pronunciation buttons, the domain chip, the "Add to list" icon button
- **Lists:** each list row (with the list name as label), the "+ New list" action, the delete action
- **Quiz:** the question text container, each option (A/B/C/D), the Next button, the exit X
- **Dialogs:** the dialog itself (with its title as label), the confirm and cancel buttons

Maybe 15 widgets total. Each one is a 2–4 line wrapper. **One PR, one afternoon.** This is the prerequisite I mentioned in the strategy discussion — without it, the test suite is fighting the framework. With it, you write tests in the natural Playwright idiom.

There's a side benefit: this same annotation improves screen reader support for blind users. So it's not "test infrastructure overhead", it's accessibility work that happens to make tests possible.

---

## 6. Worked example — the "Browse by Domain" regression test

Let's write a real test that would have caught the #603 bug we hit this morning. The bug: Browse by Domain page showed "No domains yet" even when the notebook had enriched words. The existing JaCoCo coverage gate passed; the bug shipped anyway.

### What the test needs to do

1. Open the live app
2. Make sure the notebook has at least one enriched word (capture one if not)
3. Wait long enough for enrichment to complete (~10 seconds, per the offline-first pattern)
4. Navigate to Browse by Domain
5. Assert the empty state is **not** showing
6. Assert at least one domain chip with a count > 0 is visible

### The actual test

```typescript
// File: e2e/tests/browse-by-domain.spec.ts
import { test, expect } from '@playwright/test';

test('Browse by Domain shows chips when notebook has enriched words', async ({ page }) => {
  // 1. Open the app
  await page.goto('https://wordpower-f2398.web.app');

  // 2. Capture a word that auto-enriches (medicine is a reliable domain hit)
  await page.getByRole('button', { name: 'Add Word' }).click();
  await page.getByLabel('Word input').fill('cardiology');
  await page.keyboard.press('Enter');
  await expect(page.getByText('Saved "cardiology"')).toBeVisible();

  // 3. Wait for enrichment to land — sync banner clears
  await page.getByRole('button', { name: 'Back to home' }).click();
  await expect(page.getByText('Syncing your words…')).toBeHidden({ timeout: 15000 });

  // 4. Navigate to Browse by Domain
  await page.getByRole('link', { name: 'Browse by Domain' }).click();

  // 5. Assert the empty state is NOT showing
  await expect(page.getByText('No domains yet')).toBeHidden();

  // 6. Assert at least one domain chip is visible with a count
  // (the chip text should be something like "medicine · 1")
  const anyDomainChip = page.getByRole('button').filter({ hasText: /\w+ · \d+/ });
  await expect(anyDomainChip.first()).toBeVisible();
});
```

If you ran this test against the deployed app this morning, it would have failed at step 5 ("No domains yet" was still visible). The failure output would tell you exactly:

```
Test failed: Browse by Domain shows chips when notebook has enriched words
  Expected: text "No domains yet" to be hidden
  Received: element is visible
  At: e2e/tests/browse-by-domain.spec.ts:23
  Trace: /tmp/playwright-traces/browse-by-domain.zip
```

The trace file is a complete recording of the test — every action, every network request, every console message, screenshots at every step. You open it in the trace viewer (`npx playwright show-trace /tmp/playwright-traces/browse-by-domain.zip`) and you can step through what happened frame by frame. Way better than guessing.

### Why this is more valuable than a unit test for #603

A unit test for the `BrowseByDomainPage` widget could mock the database and pass — and indeed there probably is such a test in the integration_test folder, and it probably passes. The bug isn't in the widget's logic. It's in **the entire data path from the API to the cache to the query that feeds the widget**, in the deployed environment, with real data, real headers, real worker behavior. Only an E2E test running against the actual deployed app can verify the full chain.

---

## 7. Two more worked examples — quick ones

### Console error gate (would catch #623)

This is a 10-line test that catches an entire category of regressions:

```typescript
test('no Dart exceptions on Home load', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('https://wordpower-f2398.web.app');
  await page.waitForLoadState('networkidle');

  expect(errors).toEqual([]);
});
```

Anytime any page logs anything to `console.error` or throws an unhandled exception, this test fails. The fix for #623 wouldn't have been "add this test" — it would have been "this test would have prevented #623 from ever shipping in the first place."

### The stale form leak (would catch #622)

```typescript
test('navigating away from Quick Capture disposes its form', async ({ page }) => {
  await page.goto('https://wordpower-f2398.web.app');

  // Capture a word
  await page.getByRole('button', { name: 'Add Word' }).click();
  await page.getByLabel('Word input').fill('placeholder');
  await page.keyboard.press('Enter');

  // Navigate to a word detail
  await page.getByRole('button', { name: 'Back to home' }).click();
  await page.getByRole('listitem').filter({ hasText: 'placeholder' }).click();
  await page.getByRole('link', { name: 'Details' }).click();

  // Assert only ONE form remains in the DOM
  const formCount = await page.evaluate(() => document.querySelectorAll('form').length);
  expect(formCount).toBe(1);
});
```

`page.evaluate(...)` runs JavaScript in the browser context and returns the result. It's the escape hatch when you need to check something Playwright doesn't have a built-in assertion for (DOM node counts, computed CSS, internal state).

---

## 8. Where the tests live and how they run

Recommended directory layout once we wire this up:

```
WordPower-app/
  e2e/
    playwright.config.ts        # browser, base URL, timeouts, reporters
    fixtures/
      auth.ts                   # logs in once, reuses session across tests
      cleanup.ts                # deletes test data after each test
    tests/
      pageload.spec.ts          # console-error gate, drift fallback gate
      capture.spec.ts           # Quick Capture happy path + edge cases
      word-detail.spec.ts       # Detail page renders + domain picker
      browse-by-domain.spec.ts  # the #603 regression test
      quiz.spec.ts              # 5-question MCQ end-to-end
      lists.spec.ts             # Add to list inline create + Esc dismiss
    package.json                # @playwright/test as a dev dep
```

In CI you wire one new GitHub Actions workflow that runs `npx playwright test` against the deployed staging URL after every push to `main`, or — better — against a deploy preview before merge. Roughly:

```yaml
# .github/workflows/playwright.yml (sketch)
name: E2E tests
on:
  pull_request:
    branches: [main]
jobs:
  e2e:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v5
      - run: npm ci --prefix e2e
      - run: npx playwright install chromium --with-deps
        working-directory: e2e
      - run: npx playwright test
        working-directory: e2e
        env:
          BASE_URL: ${{ vars.STAGING_URL }}
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-traces
          path: e2e/test-results/
```

When a test fails, the trace file is uploaded as a build artifact. You download it, run the trace viewer locally, see exactly what happened.

---

## 9. Things that trip people up

A short list of pitfalls, in rough order of how often they bite people:

1. **Skipping the `await`.** Every action returns a Promise. `page.click(...)` without `await` will fire-and-forget and the test will move on. Lint rule (`@typescript-eslint/no-floating-promises`) catches this; turn it on.
2. **Using sleep.** Don't `await page.waitForTimeout(2000)` to "let the page load." Use auto-waiting locators — `await expect(...).toBeVisible()` already waits up to 5 seconds. Sleeps make tests slower AND flakier.
3. **Over-broad text selectors.** `getByText('Save')` may match a button, a menu item, and a tooltip. Use `getByRole('button', { name: 'Save' })` to disambiguate.
4. **Tests that depend on previous tests.** Each test should run independently. If test B needs data created by test A, factor that creation into a fixture both can use.
5. **Testing implementation, not behavior.** "Click `div.btn-primary`" tests the markup. "Click the button named Submit" tests the user-facing behavior. Refactor markup all you want; behavior tests still pass.
6. **Forgetting auth.** If your app requires login, every test will hit the login page. Use a Playwright "storage state" file: log in once, save the cookies, every test loads from that file. Cuts ~3 seconds per test.

---

## 10. Concepts you'll see in real Playwright code but don't need yet

Listed for completeness so you know what they mean when you see them:

- **Fixtures** — shared setup objects (`auth`, `loggedInPage`, `seededDatabase`). Cleaner than `beforeEach`.
- **Page Object Model (POM)** — a class that wraps a page's locators and actions (`new QuickCapturePage(page).captureWord('foo')`). Helps when you have ~50+ tests; overkill for the first 10.
- **Projects** — run the same suite against multiple browsers (chromium / firefox / webkit). Skip for now; chromium-only is fine.
- **Sharding** — split the suite across N CI runners for speed. Worth doing once the suite is > 20 tests.
- **Reporters** — control how results are formatted (HTML, JUnit XML, GitHub Actions annotations). Default reporter is fine to start.

---

## 11. How we'll roll this out in WordPower

This is the concrete plan for adopting Playwright on this codebase, derived from the 2026-05-16 re-test results. The motivation is empirical: of the 11 bugs we tried to fix in this last cycle, 4 regressed in production and the existing test gates (JaCoCo coverage, Flutter `integration_test`) caught none of them. The categories that slipped through (deploy-infra headers, runtime DOM-level leaks, end-to-end data flow, runtime exception handling) are all things E2E catches naturally.

### Phase 0 — Semantics annotation (prerequisite, ~1 day)

**Single PR** that wraps the ~15 most-tested widgets in `Semantics`. Without this, Playwright tests have to fall back to pixel-coordinate clicks (as I had to during the smoke tests) and break on every layout tweak. With it, tests use the natural `getByRole` / `getByLabel` idioms and stay stable for months.

Concrete annotation targets:

- **Quick Capture:** the word `TextField`, the notes toggle, the notes `TextField`, the Save button, the success snackbar's "View" action
- **Word detail:** the title text, each pronunciation button (with US/UK labels), the domain chip, the "Add to list" icon button, the primary definition section, the Word Family root header
- **Lists:** each list row (label = list name), the "+ New list" inline action in the Add-to-list sheet, the Create-list dialog's Create button
- **Quiz:** the question word container, each option A/B/C/D, the Next button, the exit X icon, the results screen score text
- **Dialogs:** every modal's root with title-as-label, primary confirm button, cancel button
- **Nav (Home):** each menu link (My Words, My Lists, Browse by Domain, Discover Words, Stats)

Side benefit: this annotation is genuine accessibility work. Screen reader users get a useable app for the same cost.

File this as one GitHub issue against the app repo, parent epic = a new "E2E testing" parent or under existing infra labels. Estimate 3 points.

### Phase 1 — First 8 tests as a post-deploy gate (~12 hours)

Build the suite. Wire it as a workflow that runs against the deployed production URL after every push to `main`, after the Firebase deploy step completes. The first iteration **does not gate the merge** — it runs after the deploy and reports pass/fail to the team. This is intentional: we want to observe how the suite behaves on real traffic for a week or two before making it merge-blocking.

The 8 tests, each mapped to bugs from this conversation:

| Test file | Bugs it would have caught |
|---|---|
| `pageload-clean.spec.ts` | [#623](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/623), [#624](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/624) (console error + Drift fallback gates) |
| `capture-happy-path.spec.ts` | [#621](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/621) (red-flash regression) |
| `capture-duplicate-and-empty.spec.ts` | [#618](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/618), [#619](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/619), [#620](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/620) (duplicate View action, error-state clear, notes label) |
| `capture-no-stale-form.spec.ts` | [#622](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/622) (DOM form-leak via `evaluate`) |
| `word-detail-renders.spec.ts` | [#606](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/606), [#607](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/607), [#608](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/608), [#550](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/550), [#551](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/551) (POS, pronunciation, scroll, Word Family) |
| `domain-picker-saves.spec.ts` | [#654](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/654) (the broken domain-save we surfaced today) |
| `browse-by-domain-populated.spec.ts` | [#603](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/603) (the empty-state regression) |
| `quiz-5-questions.spec.ts` | [#605](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/605), [#609](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/609), [#598](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/598) (answer recording, transition ghosting, restart hang) |

File this as a second GitHub issue, dependent on the Phase 0 Semantics PR. Estimate 5 points.

### Phase 2 — Hardening (~1 week)

Tests against a real deployed app will hit flakiness sources that unit tests don't:

- Network jitter and occasional retries on `/api/*`
- Sync timing — the offline-first outbox can take 10–30s to settle after a capture
- Test data state — words and lists created by one test pollute the next run unless cleaned up
- The persistent "Sync failed" banner we saw today, when present, will break tests that expect a clean home screen

The hardening work:

- Add a Playwright **storage state** fixture: log in once, save the auth cookies, reuse across all tests. Cuts ~3 seconds per test and means no Google sign-in flow in the suite.
- Add a **cleanup fixture** that deletes any words / lists / domain overrides the test created. Use the backend API directly via `request.delete(...)` — faster and more reliable than navigating the UI to delete.
- Use Playwright's **`expect.poll`** for asynchronous-but-eventually-consistent assertions like "enrichment completed" or "outbox drained" — instead of hardcoded `waitForTimeout`.
- Configure a **retry policy** of 2 retries per test in CI, 0 locally. Real-world flakes get a second chance in CI without papering over genuine bugs.

### Phase 3 — Deploy-preview gating (~3 days)

Once the suite has been stable for a week or two in observation mode, promote it to a merge gate:

1. Wire Firebase Hosting **preview channels** so each PR gets a temporary `wordpower-pr-{N}.web.app` URL when CI runs.
2. Configure the Playwright workflow to run against the preview URL on every PR.
3. Add the workflow's check name to `main` branch protection as a required status check.
4. Merge is now blocked until E2E passes.

This is the end state. At this point, the kinds of regressions we hit today cannot reach production — they're caught at PR review time, before the merge button enables.

### Phase 4 — Keeping pace as the app grows

Once the suite exists, the question becomes: how do we make sure new features add new E2E tests, the way the JaCoCo (backend 80%/70%) and frontend (80%) coverage gates force unit tests on new code?

**The honest answer: don't try to mirror those gates for E2E.** Line-coverage tooling (Istanbul, c8) technically works against a Playwright run, but the deployed bundle is minified Dart→JS — the coverage report maps to symbols like `b1L.a`, not readable Dart source. The instrumentation cost is high, the report is unreadable, and the signal is weak anyway: hitting a line in an E2E test doesn't mean you've meaningfully verified the behavior on it. E2E tests are about catching integration bugs across the whole stack, not about exercising every code branch.

Instead, track **feature coverage** with a manually-maintained matrix. A single file, `e2e/COVERAGE.md`, that lists every user-visible feature and which test exercises it:

```markdown
| Feature                       | E2E test                                | Status |
|-------------------------------|-----------------------------------------|--------|
| Quick Capture: happy path     | `capture.spec.ts > happy-path`          | ✅     |
| Quick Capture: duplicate      | `capture.spec.ts > duplicate-detection` | ✅     |
| Quick Capture: empty submit   | `capture.spec.ts > empty-submit`        | ✅     |
| Word detail: pronunciation    | `word-detail.spec.ts > pronunciation`   | ✅     |
| Word detail: domain picker    | `word-detail.spec.ts > domain-picker`   | ✅     |
| Lists: create + add word      | `lists.spec.ts > create-and-add`        | ❌     |
| Lists: delete                 | —                                       | ❌     |
| Discover: dismiss card        | —                                       | ❌     |
| ...                           | ...                                     | ...    |
```

Maintained by three mechanisms:

1. **PR template question:** *"Does this PR add a user-visible feature? If so, paste the row you added to `e2e/COVERAGE.md` (or explain why an E2E test isn't needed)."* Same shape as the bug-must-touch-test gate in [#658](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/658), applied to features.
2. **CI warning (not block):** a lightweight workflow that posts a comment on `feature/*` PRs when `e2e/COVERAGE.md` hasn't changed AND no `e2e/tests/*.spec.ts` file was touched. Non-blocking — minor PRs (copy fixes, dep bumps) shouldn't be gated — but the gap becomes visible to the reviewer.
3. **Quarterly review:** scan the matrix, count `❌` rows, file issues to fill the highest-priority gaps. Roll this into the same cadence as the tech-debt audit.

If you want a coverage *number*, it's the trivial computation `✅ / (✅ + ❌)`. As of Phase 1 that's 8/8 if you only count the bugs from this conversation, but the denominator is small and biased. Over time as the feature matrix grows, both numerator and denominator grow, and the ratio tells you whether the suite is keeping pace with product work or falling behind.

**Why this works better than instrumented coverage for E2E specifically:**

- **Readable**: a human can scan the matrix in 30 seconds and know what's covered. JaCoCo HTML reports for a 200k-line bundle are unreadable.
- **Actionable**: a `❌` row is a concrete next test to write. A line-coverage gap is "go figure out which branch."
- **Cheap**: zero instrumentation, zero CI runtime overhead. The cost is one line in a markdown file per feature.
- **Aligned with what E2E actually does**: E2E is feature-level testing. Track it at the feature level.

For comparison: the JaCoCo gate at 80%/70% caught 0 of the 4 ❌ failures from today's re-test. A feature-coverage matrix would have given the team a concrete target ("Browse-by-Domain → no E2E test → file an issue") that maps directly to fewer production regressions. **Different layer of testing, different metric.**

The same approach can extend if you later add a separate matrix for **acceptance criteria coverage** (one row per closed user story's AC bullet) — but start with feature-level and only refine if you find the granularity insufficient.

### CI sketch (Phase 1 version)

A first-pass workflow targeting the post-deploy gate:

```yaml
# .github/workflows/playwright.yml
name: E2E tests
on:
  workflow_run:
    workflows: ["Deploy Web"]
    types: [completed]
    branches: [main]
jobs:
  e2e:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v5
      - run: npm ci --prefix e2e
      - run: npx playwright install chromium --with-deps
        working-directory: e2e
      - run: npx playwright test
        working-directory: e2e
        env:
          BASE_URL: https://wordpower-f2398.web.app
          TEST_USER_EMAIL: ${{ secrets.E2E_TEST_USER_EMAIL }}
          TEST_USER_PASSWORD: ${{ secrets.E2E_TEST_USER_PASSWORD }}
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-trace
          path: e2e/test-results/
```

It triggers off the existing `Deploy Web` workflow completing successfully — so E2E runs against the same bits that just went live, not against a stale local build.

### What we are explicitly NOT doing

- **Visual-regression / golden screenshots.** Brittle on Flutter web (canvas anti-aliasing, font metrics). The pain-to-value ratio is wrong. Revisit if and only if the suite is stable for 6+ months and someone has a specific pixel-fidelity concern.
- **Mobile (iOS) E2E.** Out of scope until iOS lands per the Phase 4 roadmap. Re-evaluate then; Maestro and Detox are reasonable alternatives for native flows.
- **Performance / load testing.** Already covered by the separate `k6-performance.yml` workflow.
- **Multi-browser (Firefox / WebKit).** Skip until there's evidence the app behaves differently across engines.

### Open questions to resolve before Phase 1 starts

These come up in every E2E rollout and we'll need answers before the first PR:

1. **Test account:** dedicated `e2e-bot@wordpower.test` Firebase user (recommended) or run against the dev's own account (faster to start but risks data pollution). Suggest creating the dedicated test user up front.
2. **Authentication:** Firebase Google sign-in in headless Chromium can be unreliable. Options: (a) use Firebase's `signInWithEmailAndPassword` REST API directly in a setup script and save the resulting token as storage state; (b) add a `?testAuth=...` query parameter to the app that auto-signs in for test runs in non-prod environments only. Option (a) is cleaner.
3. **Data reset:** add an admin endpoint `DELETE /api/test/reset?userId=...` (gated to test users only) so a fixture can wipe the test account at the start of each suite run. Avoids the slow per-test cleanup approach.
4. **Sync timing:** the offline-first outbox makes "did the save go through?" hard to assert deterministically. Either the test waits for a known-good signal (sync banner disappears, network shows 200) or the backend gets a fast-path endpoint for tests that skips the outbox.

### How this maps to the issue tracker

When ready to start, file two issues:

- **`a11y: add Semantics annotations to E2E-critical widgets`** — Phase 0. Estimate 3. Labels: `enhancement, frontend, accessibility`.
- **`test: bootstrap Playwright E2E suite with 8 high-value tests`** — Phase 1. Estimate 5. Depends on the Semantics issue. Labels: `enhancement, ci, testing`.

Both should reference this primer in their body for the rationale and the scenario list. Phases 2 and 3 can live as sub-tasks of the testing issue, or as follow-up tickets filed after Phase 1 lands.

---

## 12. Recommended order to actually learn

1. Run `npx playwright install` somewhere — even a scratch directory — and `npx playwright codegen https://wordpower-f2398.web.app`. Click around for 5 minutes. Watch the code Playwright writes. This shortcuts a lot of theory.
2. Take the auto-generated code and run it via `npx playwright test --ui`. Step through it. See how each action highlights an element.
3. Try writing the console-error-gate test from section 7 by hand. ~10 lines, very satisfying when it works.
4. Read [the Playwright docs on locators](https://playwright.dev/docs/locators) — the single most important concept.
5. Land the Semantics annotation PR on WordPower (separate ticket).
6. Now you can write the real suite — section 6's `browse-by-domain` test should be trivial to adapt.

Doing it in this order means each new concept builds on something you've seen working. Don't try to read the whole Playwright docs first — that's the textbook approach and it never sticks.

---

## 13. The realistic expectation

Once you've spent ~half a day writing your first 2–3 tests in `--ui` mode, the rest of the suite goes quickly. The reason Playwright has won the E2E category is that the developer experience is unusually good: the locator API is intuitive, the trace viewer is genuinely helpful, and the auto-waiting eliminates the flakiness that used to plague Selenium-style frameworks.

The hard part isn't writing tests. It's:

- **Deciding what to test.** (The 8 tests I proposed in the strategy discussion are a good starter set — high coverage, low overlap.)
- **Keeping selectors stable.** (Solved by Semantics annotations + sticking to `getByRole` / `getByLabel`.)
- **Wiring CI correctly.** (Deploy preview > prod post-deploy > local-server — pick one and commit.)

Once those are in place, the suite is something the team maintains in the background, not something you actively manage. Most weeks you don't touch it. The weeks you do touch it, it saves you the kind of cycle we just spent on #603 / #622 / #623 / #624.

---

## Further reading

- **[playwright.dev](https://playwright.dev/)** — official docs. The "Locators" and "Best Practices" pages are the only must-reads.
- **[Playwright YouTube channel](https://www.youtube.com/@Playwrightdev)** — Microsoft's official channel, weekly tips. The "VS Code extension" video is worth 10 minutes.
- **[flutter_test for web semantics](https://api.flutter.dev/flutter/semantics/SemanticsProperties-class.html)** — official `SemanticsProperties` reference. You'll want this once you start annotating widgets.
- **No external framework needed beyond Playwright itself.** Don't add Cypress, Selenium, Cucumber, etc. on top. Playwright is sufficient.
