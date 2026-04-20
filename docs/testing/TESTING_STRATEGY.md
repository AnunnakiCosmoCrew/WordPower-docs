# Testing Strategy — WordPower

> [!abstract] Summary
> WordPower uses a layered testing strategy: unit tests for logic, integration tests for the full stack, contract tests for API correctness, and fuzz tests for edge cases. Each layer catches different bugs at different speeds. A comprehensive static analysis and code quality toolchain — Checkstyle, PMD, SpotBugs, Semgrep, very_good_analysis, Spectral — enforces standards on every PR, with JaCoCo and lcov tracking coverage via a per-package ratcheting strategy.

Related: [[PROJECT#6. Technical Stack]] | [[LOCAL_FIRST_ARCHITECTURE]]

---

## Table of Contents

1. [[#1. Testing Pyramid]]
2. [[#2. Backend Testing]]
3. [[#3. Frontend Testing]]
4. [[#4. Contract Testing]]
5. [[#5. Fuzz Testing (Schemathesis)]]
6. [[#6. Static Analysis, Code Quality & Coverage Toolchain]]
7. [[#7. What Runs When]]
8. [[#8. Coverage Targets & Ratcheting]]
9. [[#9. Glossary]]

---

## 1. Testing Pyramid

```mermaid
flowchart TB
    subgraph Pyramid["Testing Pyramid (bottom = most, top = fewest)"]
        direction TB
        Fuzz["🔝 Fuzz Tests<br/>(Schemathesis)<br/>Nightly"]
        Contract["Contract Tests<br/>(spec validation + provider + consumer)<br/>Every PR"]
        Integration["Integration Tests<br/>(Testcontainers PostgreSQL, Cucumber BDD)<br/>Every PR"]
        Unit["Unit Tests<br/>(JUnit, flutter test)<br/>Every PR"]
        Static["⬇ Static Analysis<br/>(Checkstyle, SpotBugs, PMD, Semgrep, very_good_analysis)<br/>Every PR"]
    end

    Static --> Unit --> Integration --> Contract --> Fuzz
```

| Layer | Speed | Catches | Runs |
|---|---|---|---|
| **Static analysis** | ~10 sec | Code style, common bugs, security patterns | Every PR |
| **Unit tests** | ~15 sec | Logic bugs in isolated functions | Every PR |
| **Integration tests** | ~60 sec | Full stack bugs (controller → service → DB) | Every PR |
| **Contract tests** | ~10 sec | API spec drift (FE/BE disagreement) | Every PR |
| **Fuzz tests** | ~3 min | Edge cases, crashes, weird input | Nightly |

---

## 2. Backend Testing

### Unit tests (JUnit 5)

Test business logic in isolation — no Spring context, no database.

```java
@Test
void sm2_goodRating_increasesInterval() {
    var result = SrsCalculator.calculate(easeFactor, interval, repetitions, Quality.GOOD);
    assertThat(result.interval()).isGreaterThan(interval);
}
```

**What to unit test:**
- SRS algorithm calculations
- CEFR level assignment logic
- Domain keyword matching
- DTO mapping / validation
- Any pure function

**What NOT to unit test (use integration tests instead):**
- Controller request routing
- Database queries
- Flyway migrations
- External API calls

### Integration tests (Testcontainers + Cucumber BDD)

Test the full stack against a real PostgreSQL database.

**Tool:** Testcontainers spins up a PostgreSQL Docker container. Cucumber BDD provides readable scenarios.

```gherkin
Feature: Word CRUD

  Scenario: Save a new word
    Given I am authenticated as "mert@example.com"
    When I save the word "ubiquitous"
    Then the response status is 201
    And the word is stored in the database
    And enrichment is triggered
```

**What integration tests cover:**
- Full request → controller → service → repository → PostgreSQL round trip
- Flyway migrations run cleanly
- JSONB serialization/deserialization from PostgreSQL
- Transaction behavior
- Auth filter rejects invalid tokens

**Why Testcontainers, not H2:**

WordPower uses PostgreSQL-specific features that H2 doesn't support:

| Feature | PostgreSQL | H2 |
|---|---|---|
| `JSONB` columns | ✅ Native | ❌ Not supported |
| `ON CONFLICT` upsert | ✅ | ⚠️ Different syntax |
| `GIN` indexes | ✅ | ❌ |
| Flyway migrations | ✅ Run as-is | ❌ Need separate files |

H2 would require separate migrations and give false confidence — tests pass on H2, app crashes on real PostgreSQL.

#### How Testcontainers actually works

Testcontainers is a ==Java library==, not a CI plugin or Docker Compose setup. It's a dependency in `build.gradle`. Anywhere Gradle runs + Docker is available = Testcontainers works. The same `./gradlew check` runs identically on your laptop and in CI.

##### The lifecycle

```mermaid
flowchart TB
    Gradle["./gradlew test"] --> JUnit["JUnit finds<br/>@Testcontainers annotation"]
    JUnit --> Start["Testcontainers starts<br/>postgres:16 container<br/>on random port"]
    Start --> Flyway["Flyway runs<br/>V1__initial_schema.sql<br/>against the container"]
    Flyway --> Tests["Tests execute<br/>real SQL against<br/>real PostgreSQL"]
    Tests --> Destroy["Container stopped<br/>and removed"]
```

##### Local vs CI — zero difference

| Aspect | Local (`./gradlew test`) | CI (GitHub Actions) |
|---|---|---|
| Docker source | Docker Desktop on your Mac | Pre-installed on runner |
| Image cache | Persists across runs | Persists within workflow |
| Container port | Random (avoids conflicts) | Random |
| Flyway migrations | Run against container | Same |
| Config needed | Docker Desktop running | Nothing — works out of the box |
| Test code | ==Identical== | ==Identical== |

No `services:` block in GitHub Actions. No `docker-compose.yml`. Testcontainers manages the container lifecycle inside the JVM process.

##### What the test code looks like

```java
@SpringBootTest
@Testcontainers
class WordRepositoryIntegrationTest {

    // Testcontainers manages this — starts before tests, stops after
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("wordpower_test")
        .withUsername("test")
        .withPassword("test");

    // Tell Spring to use the container's dynamic port
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    WordRepository wordRepository;

    @Test
    void savesAndRetrievesWord() {
        var word = new UserWord("ubiquitous", "user-123");
        wordRepository.save(word);

        var found = wordRepository.findByWordAndUserId("ubiquitous", "user-123");
        assertThat(found).isPresent();
        assertThat(found.get().getWord()).isEqualTo("ubiquitous");
    }
}
```

**Step by step:**

| Step | What happens | Who does it |
|---|---|---|
| 1 | JUnit finds `@Testcontainers` annotation | JUnit |
| 2 | Finds `@Container` field → starts `postgres:16` Docker container | Testcontainers |
| 3 | Container picks a random available port (e.g., 54321) | Docker |
| 4 | `@DynamicPropertySource` injects `jdbc:postgresql://localhost:54321/wordpower_test` into Spring | Spring + Testcontainers |
| 5 | Spring Boot starts with the test datasource | Spring |
| 6 | Flyway runs migrations against the container | Flyway |
| 7 | Test methods execute real SQL against real PostgreSQL | Your test code |
| 8 | Test class finishes → container stopped and removed | Testcontainers |

##### Performance: the cold start

| Operation | Time | Happens when |
|---|---|---|
| Docker image pull (`postgres:16`) | 10–30 sec | First time only (cached after) |
| Container start | 3–5 sec | Every test run |
| Flyway migrations | 1–2 sec | Every test run |
| Actual tests | 1–10 sec | Every test run |

**First run:** ~40 sec. **Subsequent runs:** ~10 sec (image cached).

##### Optimization: one container for the entire test suite

Without optimization, each test class starts a new container. With a shared base class, ==one container serves all test classes==:

```java
public abstract class BaseIntegrationTest {

    static final PostgreSQLContainer<?> postgres;

    static {
        postgres = new PostgreSQLContainer<>("postgres:16")
            .withDatabaseName("wordpower_test");
        postgres.start();  // starts ONCE, reused by all subclasses
    }

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}

// All integration tests extend this — one container for the entire suite
class WordRepositoryTest extends BaseIntegrationTest { ... }
class WordServiceTest extends BaseIntegrationTest { ... }
class EnrichmentPipelineTest extends BaseIntegrationTest { ... }
```

One container start (~5 sec) serves 50+ test classes.

---

## 3. Frontend Testing

### Widget tests (flutter test)

Test individual widgets and screens in isolation.

```dart
testWidgets('Quick Capture saves word on Enter', (tester) async {
  await tester.pumpWidget(ProviderScope(child: QuickCaptureScreen()));
  await tester.enterText(find.byType(TextField), 'ubiquitous');
  await tester.testTextInput.receiveAction(TextInputAction.done);
  await tester.pump();

  expect(find.text('Saved!'), findsOneWidget);
});
```

**What to widget test:**
- Quick Capture: save, duplicate, empty validation
- Word list: rendering, search, delete
- Flashcard: flip animation, navigation, progress
- Dashboard: word count, empty state
- Word Detail View: all enrichment fields display

### State management tests

Test Riverpod providers and business logic without widgets.

```dart
test('WordNotifier adds word and triggers enrichment', () async {
  final container = ProviderContainer();
  final notifier = container.read(wordNotifierProvider.notifier);

  await notifier.addWord('ubiquitous');

  final words = container.read(wordListProvider);
  expect(words, hasLength(1));
  expect(words.first.word, equals('ubiquitous'));
});
```

---

## 4. Contract Testing

Contract testing ensures the **OpenAPI spec**, the **backend implementation**, and the **frontend client SDK** all agree. Three layers:

### Layer 1: Spec validation

**Tool:** Spectral (linting) + oasdiff (breaking change detection)

**What it checks:**
- Is `api/openapi.yaml` valid OpenAPI 3.0?
- Are all properties `camelCase`? Paths `kebab-case`?
- Do all error responses use the standard `ErrorResponse` schema?
- Do POST/PUT define 400? Do all endpoints define 401? Do `{id}` endpoints define 404?
- Did this PR introduce a breaking change (field removed, type changed)?

**Severity policy:**
- `error` → CI fails, merge blocked (correctness, consistency, error standards)
- `warn` → shown in PR, merge allowed (documentation)

**Runtime:** ~5 seconds

**Issue:** #115

### Layer 2: Provider-side tests

**Tool:** `@WebMvcTest` + `@MockBean` + OpenAPI response validator

**What it checks:** does the Spring Boot controller produce JSON responses that match the OpenAPI spec?

```java
@WebMvcTest(WordsApiController.class)
class WordCrudContractTest {

    @Autowired MockMvc mockMvc;
    @MockBean WordService wordService;  // no DB, no Docker

    @Test
    void createWord_responseMatchesContract() throws Exception {
        when(wordService.createWord(any(), any())).thenReturn(fakeWordDto());

        var result = mockMvc.perform(post("/api/words")
                .contentType(APPLICATION_JSON)
                .content("{\"word\": \"ubiquitous\"}"))
            .andExpect(status().isCreated())
            .andReturn();

        // Validates ENTIRE response against openapi.yaml
        validator.assertResponseMatchesSpec(result, "POST", "/api/words");
    }
}
```

**Key design decision:** uses `@WebMvcTest` with mocked services — ==no database, no Docker, no Testcontainers==. Contract tests verify response shape, not business logic. Integration tests (#89) cover the full stack.

| Concern | Contract test | Integration test |
|---|---|---|
| Response matches spec schema | ✅ | ❌ |
| All required fields present | ✅ | ❌ |
| Error responses match `ErrorResponse` | ✅ | ❌ |
| SQL queries correct | ❌ | ✅ |
| JSONB works | ❌ | ✅ |

**Runtime:** ~5 seconds

**Issue:** #113

### Layer 3: Consumer-side tests

**Tool:** `flutter test` with JSON fixtures

**What it checks:** can the generated Dart client SDK correctly deserialize real backend responses?

```dart
test('WordResponse deserializes correctly', () {
  final json = jsonDecode(File('test/fixtures/word_response.json').readAsStringSync());
  final word = WordResponse.fromJson(json);

  expect(word.id, equals(42));
  expect(word.definitions, hasLength(1));
  expect(word.synonyms, containsAll(['omnipresent', 'pervasive']));
  expect(word.cefrLevel, equals('C1'));
});

test('handles missing optional fields', () {
  fixture.remove('synonyms');
  final word = WordResponse.fromJson(fixture);
  expect(word.synonyms, isNull);
  expect(word.word, equals('ubiquitous'));  // required fields still work
});
```

**What it catches that Layer 2 doesn't:**
- Dart generator bug in deserialization code
- Date format mismatch between Java and Dart serializers
- Null handling differences between generators
- Field renamed in BE but Dart model not regenerated

**Runtime:** ~5 seconds

**Issue:** #114

### How the three layers work together

```mermaid
flowchart TB
    Spec["openapi.yaml<br/>(the contract)"]
    L1["Layer 1: Spec validation<br/>Is the spec valid?"]
    L2["Layer 2: Provider tests<br/>Does BE match the spec?"]
    L3["Layer 3: Consumer tests<br/>Can FE read BE responses?"]

    Spec --> L1
    Spec --> L2
    Spec --> L3

    L1 -->|"Fail"| Block["❌ Merge blocked"]
    L2 -->|"Fail"| Block
    L3 -->|"Fail"| Block
```

---

## 5. Fuzz Testing (Schemathesis)

**Tool:** Schemathesis — auto-generates hundreds of API inputs from the OpenAPI spec

**What it does:** reads `api/openapi.yaml`, generates valid and invalid inputs for every endpoint, fires them at a running API, checks for crashes and spec violations.

**What it catches that other tests don't:**

| Input | Would you write a test? | Schemathesis tests it? |
|---|---|---|
| `it's` (apostrophe) | Probably not | ✅ |
| `résumé` (accents) | Probably not | ✅ |
| `naïve` (diacritics) | Probably not | ✅ |
| 10,000-character word | No | ✅ |
| `'; DROP TABLE users--` | Maybe | ✅ |
| Empty string | Yes | ✅ |
| Null fields in every combination | No | ✅ |

**When it runs:** nightly at 3 AM UTC (too slow for every PR)

**Notification on failure:** auto-creates a GitHub Issue with `bug` label, failure details, and link to the run. Shows on the project board and triggers email notification — ==impossible to miss==.

```mermaid
flowchart LR
    Nightly["3 AM: Schemathesis"] --> Pass{"Pass?"}
    Pass -->|"Yes"| Silent["✅ Silent"]
    Pass -->|"No"| Issue["🔴 Auto-creates<br/>GitHub Issue"]
    Issue --> Board["Project board"]
    Issue --> Email["Email notification"]
```

**Runtime:** ~3 minutes (needs running server + Testcontainers PostgreSQL)

**Issue:** #133

---

## 6. Static Analysis, Code Quality & Coverage Toolchain

### How static analysis works

Static analysis tools read your code **without executing it** and check it against a set of configured rules. ==*"Static"* means the code is never run — the tool inspects the code as written (or as compiled) and reports violations.==

At a high level, every static analysis tool follows the same loop:

1. **Parse** — read source code (or compiled bytecode) and build an internal model
2. **Analyze** — walk the model and apply rules
3. **Report** — emit findings (file, line number, rule violated, severity)

The depth of the internal model determines what the tool can catch. There are four levels, from shallow to deep:

#### Level 1: Text / token matching

The tool splits source code into tokens (keywords, identifiers, operators, whitespace) and checks structural patterns against them.

- **Can catch:** formatting violations, naming conventions, import ordering, brace placement
- **Cannot catch:** logic bugs, null dereferences, unused variables across scopes
- **Analogy:** spell-checking and grammar-checking a document without understanding its meaning
- **WordPower tools at this level:** Checkstyle, dart format, Spectral

#### Level 2: AST (Abstract Syntax Tree) + rule engine

The tool parses source into a full syntax tree — a structured representation of the code's grammar — and walks the tree applying rules. It understands code structure (methods, classes, control flow blocks) but does not simulate execution.

- **Can catch:** cyclomatic complexity, unused variables within a method, empty catch blocks, missing switch defaults, anti-patterns
- **Cannot catch:** null dereferences across method calls, resource leaks that span multiple methods, concurrency bugs
- **Analogy:** understanding the sentence structure of a document, but not reasoning about what the sentences mean together
- **WordPower tools at this level:** PMD, Semgrep, very_good_analysis / flutter analyze

#### Level 3: Bytecode + data flow analysis

The tool reads compiled bytecode (not source) and builds a **control flow graph** — a map of every possible execution path through the code. It then simulates data flow along these paths to find bugs.

- **Can catch:** null pointer dereferences ("variable X is null at line 50 because of the branch at line 30"), resource leaks across method boundaries, concurrency issues, security vulnerabilities mapped to CWE categories
- **Cannot catch:** runtime-only issues (external API behavior, configuration errors, race conditions that depend on timing)
- **Analogy:** reasoning about what a document *means* by tracing the logical connections between its parts
- **WordPower tools at this level:** SpotBugs (+ FindSecBugs, sb-contrib plugins)

#### Level 4: Runtime instrumentation (coverage)

The tool instruments compiled bytecode to **record which lines and branches actually execute** during tests. It doesn't find bugs directly — it finds **untested code** where bugs could hide.

- **Can answer:** "was line 50 executed by any test?", "were both branches of the if-statement at line 30 tested?"
- **Cannot answer:** "is line 50 correct?"
- **Analogy:** highlighting which pages of a textbook a student actually read, without judging whether they understood them
- **WordPower tools at this level:** JaCoCo, lcov

#### Why WordPower uses multiple levels

Each level catches different things. A tool at one level is blind to findings at another:

```
Text/token     →  Checkstyle catches "wrong indent"      → PMD, SpotBugs don't care
AST            →  PMD catches "empty catch block"         → Checkstyle can't see it
Bytecode       →  SpotBugs catches "null deref path"      → PMD can't trace across methods
Instrumentation → JaCoCo catches "untested code"          → none of the above check this
```

The same principle applies to source-level vs bytecode-level security scanning. Semgrep (AST-level, reads source) and SpotBugs+FindSecBugs (bytecode-level, reads `.class` files) cover **disjoint vulnerability surfaces** — a finding that one misses, the other catches. This is why both exist in the pipeline rather than picking one.

---

All tools below are **hard-gated** in CI unless noted otherwise — a violation blocks the merge.

### Backend

#### Checkstyle 10.21.4 — Style enforcement (Level 1: token matching)

| Setting         | Value                                                |
| --------------- | ---------------------------------------------------- |
| **Config**      | `backend/config/checkstyle/checkstyle.xml`           |
| **Baseline**    | Google Java Style (modified)                         |
| **Indent**      | 4 spaces (Google default is 2)                       |
| **Line length** | 120 characters (Google default is 100)               |
| **Policy**      | `maxWarnings = 0` — warnings are treated as failures |
| **Issue**       | #21 ✅                                                |

Key rules enforced:
- Unused, wildcard, and redundant imports
- Naming conventions (types, methods, constants, packages)
- Brace style
- Empty catch blocks require a comment
- Missing switch default
- equals/hashCode consistency

Reports: `build/reports/checkstyle/` (HTML + XML).

#### PMD 7.23.0 — Code quality rules (Level 2: AST + rule engine)

| Setting | Value |
|---|---|
| **Config** | `backend/config/pmd/ruleset.xml` |
| **Rulesets** | `bestpractices`, `errorprone`, `codestyle` |
| **Policy** | `isIgnoreFailures = false` — findings fail the build |
| **Console output** | Enabled (violations visible in CI log) |
| **Issue** | #22 ✅ |

Notable exclusions (with rationale):

| Excluded rule | Why |
|---|---|
| `AbstractClassWithoutAbstractMethod` | Spring `@Configuration` classes are abstract by convention |
| `GuardLogStatement` | Await logging facade standardization |
| `UnitTestShouldIncludeAssert` | Spring `contextLoads` smoke tests are valid without asserts |
| `AvoidCatchingGenericException` | Necessary in some spots; code review catches misuse |
| `AtLeastOneConstructor` | Spring Boot main classes |
| `MethodArgumentCouldBeFinal`, `LocalVariableCouldBeFinal` | Stylistic noise; await final-by-default convention |
| `CommentDefaultAccessModifier` | JUnit 5 uses package-private by convention |
| `ShortVariable`, `LongVariable` | PMD's heuristics ignore naming context |
| `OnlyOneReturn` | Contested style preference; early returns improve readability |

Reports: `build/reports/pmd/` (HTML + XML).

#### SpotBugs 4.9.8 — Bug patterns & security (Level 3: bytecode + data flow)

| Setting | Value |
|---|---|
| **Config** | `backend/config/spotbugs/spotbugs-exclude.xml` |
| **Effort** | `MAX` (runs all analysis passes) |
| **Report level** | `MEDIUM` confidence (LOW filtered out — too noisy) |
| **Policy** | `ignoreFailures = false` — findings fail the build |
| **Plugins** | FindSecBugs 1.14.0 (CWE-mapped security), sb-contrib 7.7.4 (performance + design) |
| **Issue** | #22 ✅ |

**Defense-in-depth:** SpotBugs operates on compiled bytecode. Semgrep (below) operates on source code. Together they cover disjoint vulnerability surfaces — a finding that one misses, the other catches.

Documented false-positive suppressions:
- `FirebaseAuthenticationFilter` / `FirebaseAuthenticationToken` — defensive-copying false positives on Spring-managed singletons
- `SecurityConfig` — OCP_OVERLY_CONCRETE_PARAMETER on Firebase filter injection
- `WordsController` / `WordsService` — EI_EXPOSE_REP2 on constructor injection
- `com.wordpower.api.gen.*` — all findings excluded (generated code)

Reports: `build/reports/spotbugs/` (HTML + XML).

#### Semgrep 1.159.0 — Source-level SAST (Level 2: AST pattern matching)

| Setting | Value |
|---|---|
| **Config** | `.github/workflows/semgrep.yml` |
| **Container** | `semgrep/semgrep:1.159.0` (pinned) |
| **Rulesets** | `p/security-audit`, `p/java`, `p/owasp-top-ten` |
| **Policy** | `--error` — any finding fails the job |
| **Schedule** | PR + push to `main` + weekly Monday 06:30 UTC |
| **Caching** | `~/.semgrep` cached per workflow file hash |
| **Issue** | #23 ✅ |

Skips Dependabot PRs (no access to secrets context). The weekly cron scan catches new rules against `main` between PRs. SARIF report uploaded as workflow artifact (downloadable from the Actions tab).

#### JaCoCo 0.8.12 — Code coverage (Level 4: runtime instrumentation)

| Setting | Value |
|---|---|
| **Config** | `backend/build.gradle.kts` (lines 200–345) |
| **Unit target** | 80% INSTRUCTION per package |
| **Component target** | 70% INSTRUCTION per package |
| **Mode** | **Report-only** (verification rules wired but disabled — one-line flip to enforce) |
| **Issue** | #25 ✅ |

Two separate reports:
- **Unit:** `build/reports/jacoco/unit/jacocoTestReport.xml` + HTML (covers `test` task)
- **Component:** `build/reports/jacoco/component/jacocoComponentTestReport.xml` + HTML (covers `componentTest` task — Cucumber BDD)

Exclusions from coverage measurement:
- `**/*$*` — synthetic classes, lambdas, inner classes
- `com/wordpower/api/gen/**` — generated OpenAPI stubs

Aggregate convenience task: `./gradlew coverage` runs both report tasks.

CI integration: a Python script (`.github/scripts/jacoco_summary.py`) parses JaCoCo XML and renders a coverage summary in the GitHub Step Summary. Both HTML reports are uploaded as artifacts (30-day retention).

**Ratcheting plan:** per-package enforcement tracked on WP-25 issue (open checklist). As feature modules accumulate tests, coverage verification is flipped to `enabled = true` package-by-package — never all-at-once.

#### Dependabot — Dependency vulnerability scanning

| Setting | Value |
|---|---|
| **Config** | `.github/dependabot.yml` |
| **Ecosystems** | Gradle (backend), pub (frontend), GitHub Actions |
| **Issue** | #44 ✅ |

### Frontend

#### very_good_analysis 10.2.0 + flutter analyze — Lint rules (Level 2: AST + rule engine)

| Setting | Value |
|---|---|
| **Config** | `frontend/analysis_options.yaml` |
| **Baseline** | `very_good_analysis` (~140 lint rules) |
| **Strict mode** | `strict-casts: true`, `strict-inference: true`, `strict-raw-types: true` |
| **Error promotion** | `missing_return` and `missing_required_param` promoted to errors |
| **CI command** | `flutter analyze --no-fatal-infos` |

Project-specific overrides from the very_good_analysis baseline:

| Override | Reason |
|---|---|
| `prefer_relative_imports: true` | In-package imports read better as relative |
| `public_member_api_docs: false` | This is an app, not a library — doc comments on every public member is overkill |
| `lines_longer_than_80_chars: false` | Modern screens; 80-char limit causes unnecessary wrapping |
| `sort_pub_dependencies: false` | Dependencies grouped by purpose, not alphabetically |
| `specify_nonobvious_property_types: false` | Riverpod generics make explicit types excessively long |

Analysis exclusions (generated code): `*.g.dart`, `*.freezed.dart`, `*.config.dart`, `lib/api/generated/**`.

#### dart format — Formatting enforcement (Level 1: token matching)

CI runs `dart format --set-exit-if-changed .` — any formatting drift fails the build. No configuration needed; Dart's formatter is opinionated and deterministic.

#### Coverage (lcov) — 80% target (Level 4: runtime instrumentation)

| Setting | Value |
|---|---|
| **CI command** | `flutter test --coverage` |
| **Target** | 80% line coverage |
| **Mode** | **Report-only** (`::warning::` on below-target, never fails CI) |
| **Issue** | #28 ✅ |

Coverage processing pipeline:
1. `flutter test --coverage` produces `coverage/lcov.info`
2. `lcov --remove` strips generated code (`*.g.dart`, `*.freezed.dart`, `*.config.dart`, `*/api/generated/*`)
3. `genhtml` produces an HTML report (uploaded as artifact, 30-day retention)
4. Coverage summary parsed and rendered in GitHub Step Summary

**Ratcheting plan:** per-module enforcement tracked on WP-28 issue (open checklist). Same approach as backend — flip to enforced per-module as tests land.

### API

#### Spectral 6.11.1 — OpenAPI spec linting (Level 1: token matching)

| Setting | Value |
|---|---|
| **Config** | `api/.spectral.yaml` |
| **Extends** | `spectral:oas` (Stoplight's built-in OpenAPI rules) |
| **Policy** | `--fail-severity error` — spec errors block the merge |
| **CI workflow** | `.github/workflows/openapi-ci.yml` |

Catches:
- Invalid `$ref` references
- Malformed examples
- Missing operationIds
- Unused components
- Style violations

### Generated code exclusions

Every quality tool must exclude generated code — otherwise findings are noise that can't be fixed. Here's the exclusion map:

| Generator output | Checkstyle | PMD | SpotBugs | JaCoCo | flutter analyze | lcov |
|---|---|---|---|---|---|---|
| OpenAPI Spring stubs (`com.wordpower.api.gen.*`) | ✅ excluded | ✅ excluded | ✅ excluded | ✅ excluded | — | — |
| OpenAPI Dart client (`lib/api/generated/`) | — | — | — | — | ✅ excluded | ✅ excluded |
| Drift ORM (`*.g.dart`) | — | — | — | — | ✅ excluded | ✅ excluded |
| Freezed (`*.freezed.dart`) | — | — | — | — | ✅ excluded | ✅ excluded |
| build_runner (`*.config.dart`) | — | — | — | — | ✅ excluded | ✅ excluded |
| Synthetic/lambda classes (`**/*$*`) | — | — | — | ✅ excluded | — | — |

### Quality gates summary

| Tool | Version | Gate | Threshold | Scope |
|---|---|---|---|---|
| Checkstyle | 10.21.4 | **Hard** (merge blocked) | Zero warnings | Backend |
| PMD | 7.23.0 | **Hard** (merge blocked) | Zero violations | Backend |
| SpotBugs + FindSecBugs | 4.9.8 + 1.14.0 | **Hard** (merge blocked) | Zero MEDIUM+ findings | Backend |
| Semgrep | 1.159.0 | **Hard** (merge blocked) | Zero findings | Backend |
| JaCoCo (unit) | 0.8.12 | Report-only | 80% INSTRUCTION / package | Backend |
| JaCoCo (component) | 0.8.12 | Report-only | 70% INSTRUCTION / package | Backend |
| very_good_analysis | 10.2.0 | **Hard** (merge blocked) | Zero errors + warnings | Frontend |
| dart format | Dart SDK | **Hard** (merge blocked) | Zero formatting drift | Frontend |
| lcov coverage | — | Report-only | 80% line | Frontend |
| Spectral | 6.11.1 | **Hard** (merge blocked) | Zero errors | API spec |
| Dependabot | — | PR auto-created | Known CVEs | All |

---

## 7. What Runs When

### Every PR

```
┌─────────────────────────────────────────┐
│ frontend-ci           (~50 sec total)   │
│  ├── flutter analyze                    │
│  ├── dart format --set-exit-if-changed  │
│  ├── flutter test (unit + widget +      │
│  │    consumer contract fixtures)       │
│  └── coverage report                   │
├─────────────────────────────────────────┤
│ backend-ci            (~90 sec total)   │
│  ├── checkstyle + spotbugs + pmd       │
│  ├── unit tests                        │
│  ├── integration tests (Testcontainers) │
│  ├── provider contract tests (@WebMvc)  │
│  └── jacoco coverage report            │
├─────────────────────────────────────────┤
│ spec-validation       (~5 sec total)    │
│  ├── spectral lint openapi.yaml        │
│  └── oasdiff breaking change check     │
├─────────────────────────────────────────┤
│ semgrep               (~15 sec)         │
│  └── security pattern scan             │
└─────────────────────────────────────────┘

All run in PARALLEL → wall clock ~90 seconds
```

> [!tip] Smart skipping (WP-62)
> `dorny/paths-filter` skips irrelevant CI jobs. A PR that only changes frontend code won't run backend CI, and vice versa. Spec validation only runs when `api/` or `.spectral.yaml` changes.

### Nightly

```
┌─────────────────────────────────────────┐
│ schemathesis          (~3 min)          │
│  ├── start API + Testcontainers PG     │
│  ├── auto-generate inputs from spec    │
│  ├── fire at every endpoint            │
│  └── on failure → create GitHub Issue  │
└─────────────────────────────────────────┘
```

### Before release

- Full Schemathesis run with higher `--hypothesis-max-examples`
- Manual exploratory testing
- Beta tester feedback (Phase 6)

---

## 8. Coverage Targets & Ratcheting

### Current targets

| Layer | Metric | Target | Mode | Issue |
|---|---|---|---|---|
| Backend unit | INSTRUCTION per package | 80% | Report-only | #25 |
| Backend component | INSTRUCTION per package | 70% | Report-only | #25 |
| Frontend | Line coverage | 80% | Report-only | #28 |

> [!info] Why report-only, not enforced
> Hard coverage gates incentivize writing meaningless tests to hit a number. Report-only shows the trend without blocking legitimate PRs that happen to touch uncovered code. If coverage drops significantly, it's visible in the PR and can be discussed.

### Ratcheting strategy

Coverage enforcement is **per-package** and **incremental**. As a feature module accumulates enough tests to consistently meet the target, its JaCoCo verification rule (or lcov threshold check) is flipped from report-only to enforced. This avoids two failure modes:

1. **Global gate too early** — blocks unrelated PRs that happen to touch uncovered legacy code
2. **Never enforced** — report-only forever, coverage silently declines

The ratchet only moves forward — once a package is enforced, it stays enforced.

#### Backend ratchet (tracked on WP-25)

JaCoCo verification rules in `build.gradle.kts` are pre-wired per package with `enabled = false`. Enforcement = flipping one boolean:

| Package | Unit (80%) | Component (70%) |
|---|---|---|
| `com.wordpower.api.domain.*` | ⬜ Pending | — |
| `com.wordpower.api.application.*` | ⬜ Pending | — |
| `com.wordpower.api.web.*` | — | ⬜ Pending |
| `com.wordpower.api.persistence.*` | — | ⬜ Pending |

#### Frontend ratchet (tracked on WP-28)

lcov threshold check per module — currently all report-only:

| Module | Line (80%) |
|---|---|
| `lib/data/database/` | ⬜ Pending |
| `lib/features/capture/` | ⬜ Pending |
| (extend per feature module as code lands) | |

### CI visibility

Both backends and frontend CI render coverage summaries in the **GitHub Step Summary** on every PR. HTML reports are uploaded as **workflow artifacts** (30-day retention) for drill-down inspection. When coverage drops below target, CI emits a `::warning::` annotation — visible in the PR checks but not blocking.

---

## 9. Glossary

| Term | Definition |
|---|---|
| **Unit test** | Tests a single function or class in isolation, no external dependencies |
| **Integration test** | Tests the full stack (controller → service → DB) against a real database |
| **Contract test** | Verifies API responses match the OpenAPI spec — catches FE/BE disagreement |
| **Fuzz test** | Auto-generates random inputs to find crashes and edge cases |
| **Provider test** | Contract test on the backend — "does my API return what the spec says?" |
| **Consumer test** | Contract test on the frontend — "can my client deserialize what the API sends?" |
| **Testcontainers** | Library that spins up Docker containers (PostgreSQL, Redis, etc.) for integration tests |
| **@WebMvcTest** | Spring annotation that loads only the controller layer — fast, no DB needed |
| **Schemathesis** | Open-source tool that reads an OpenAPI spec and auto-generates API test cases |
| **Spectral** | OpenAPI spec linter — validates structure, naming conventions, and custom rules |
| **oasdiff** | Detects breaking changes between two versions of an OpenAPI spec |
| **JaCoCo** | Java code coverage tool — measures which lines/branches are executed by tests |
| **Cucumber BDD** | Behavior-driven testing framework — tests written as human-readable Gherkin scenarios |
| **WireMock** | HTTP mock server for simulating external APIs (Free Dictionary, Oxford) in tests |
| **Fixture** | A static JSON file representing an expected API response, used in consumer tests |
