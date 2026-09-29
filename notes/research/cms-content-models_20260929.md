# CMS content models: WordPress, Drupal, static-site generators

Research notes for vocabulary-building on our FastAPI + SQLite admin console
that renders to static HTML for GitHub Pages. Goal: precise terms for
CONTEXT.md / spec, not exhaustive coverage. Every claim below is cited to the
primary doc page that owns it (developer.wordpress.org, drupal.org,
jekyllrb.com, gohugo.io). No convention existed yet for `notes/research/`
before this file — starting one here, alongside the other student notes
(`cms-field-notes.md`, `client-brief.md`).

---

## WordPress

**Content type.** WordPress calls a content type a **post type** — "WordPress
stores the Post Types in the `posts` table," and the platform ships with
built-in post types (post, page, attachment, etc.) alongside the ability to
`register_post_type()` custom ones. All post types share one underlying
database table structure, so "post type" is really a classification column
on a single unified content table, not a separate schema per type.
Source: [Post Types](https://developer.wordpress.org/plugins/post-types/) (developer.wordpress.org).

**Draft vs. published.** WordPress models this as a **post status**, a
string field on each post. `get_post_status()` documents the standard values:
`publish`, `future` (scheduled — shown as "Scheduled" in the editor UI),
`draft`, `pending` (pending review), `private`, plus internal values `trash`,
`auto-draft`, and `inherit` (used by attachments, which inherit their
parent's status). Plugins can register further custom statuses.
Source: [`get_post_status()`](https://developer.wordpress.org/reference/functions/get_post_status/) (developer.wordpress.org).
Creating a `private` or `publish`/scheduled post requires the `publish_posts`
capability — publishing is gated by capability, not just a status flag.
Source: [WordPress post status search summary, developer.wordpress.org reference pages].

**Slug / permalink.** Not documented on the Post Types overview page itself
(checked — it doesn't mention `post_name` or permalinks), but is visible
behaviorally: the slug is the URL-safe identifier generated from the title,
and the permalink is the full URL built from the site's permalink structure
plus that slug. (See field notes: slug auto-fills from title as you type.)

**Taxonomy.** "A Taxonomy is a fancy word for the classification/grouping of
things. Taxonomies can be hierarchical (with parents/children) or flat,"
stored in a `term_taxonomy` table, with individual grouping values called
**terms** stored separately (e.g., taxonomy `Art` might have terms `Modern`,
`18th Century`). Built-in taxonomies are Category (hierarchical) and Tag
(flat) — not detailed in this specific doc page but standard WP knowledge.
Source: [Taxonomies](https://developer.wordpress.org/plugins/taxonomies/) (developer.wordpress.org).

**Roles vs. capabilities.** WordPress explicitly separates the two: a
**role** is "a set of capabilities for a user. For example, what the user
may see and do in his dashboard," and a **capability** "define[s] what a
role can and can not do: edit posts, publish posts, etc." Roles and
capabilities are stored in the `options` table under `user_roles`. Built-in
roles: Super Admin, Administrator, Editor, Author, Contributor, Subscriber.
Example capabilities named on this page: `read`, `edit_posts`,
`edit_others_posts`, `publish_posts`, `delete_posts`, `upload_files`. The
page documents the mechanism (`add_role()`, capability checks) rather than
printing a role-to-capability matrix.
Source: [Roles and Capabilities](https://developer.wordpress.org/plugins/users/roles-and-capabilities/) (developer.wordpress.org).

**Theme.** "A WordPress theme represents the design of your website. It can
control everything from colors, to fonts, to the entire layout." Crucially:
"Themes take the content stored by WordPress and display it in the
browser" — theme and content are explicitly separate layers, with block
themes using HTML block templates and classic themes using PHP templates.
Source: [What is a Theme?](https://developer.wordpress.org/themes/getting-started/what-is-a-theme/) (developer.wordpress.org).

**Headless.** The REST API handbook doesn't use the word "headless"
directly, but describes the pattern: the API lets you "bring your WordPress
content into completely separate applications" and "send and receive JSON
data ... to query, modify and create content on your site," decoupling
WordPress-as-content-store from whatever renders the front end (a JS app, a
mobile app, etc.).
Source: [REST API Handbook](https://developer.wordpress.org/rest-api/) (developer.wordpress.org).

**Publishing model.** Because WordPress is server-+ database-backed, "publish"
is a status transition on a row that a live PHP process reads on every
request. There's no build step: flipping `draft` → `publish` (or the
scheduler firing on a `future` post) makes the content visible on the next
page load, gated by the `publish_posts` capability check.

---

## Drupal

**Content model: entity, bundle, content type, field.** Drupal's model is a
layer more abstract than WordPress's. A **(content) entity** is "an item of
content data, which can consist of text, HTML markup, images, attached
files, and other data that is intended to be displayed to site visitors."
Entities group into **entity types** (Content item, Comment, User, etc.),
and many entity types divide further into **entity subtypes** — a
**content type** is specifically "an entity subtype for the 'Content item'
entity type," representing a category like blog post or basic page, each
with its own configured set of fields. Within entities, data lives in
individual **fields**, "each of which holds one type of data, such as
formatted or plain text, images or other files, or dates" — fields are
assigned per subtype so every instance of that subtype shares the same
structure.
Source: [2.4 Planning Content Types](https://www.drupal.org/docs/user_guide/en/planning-data-types.html) (drupal.org User Guide).

**Draft vs. published.** Out of the box (no extra modules), a Drupal node
has a simple binary **Published** checkbox/status: "By default, only
administrators may view unpublished content, while published content is
accessible for anyone." A content type's base configuration determines
whether newly created content of that type defaults to published.
Source: [Publishing Options / 2.5 Planning your Content Structure](https://www.drupal.org/docs/user_guide/en/planning-structure.html) (drupal.org User Guide).

For real draft/review workflows, Drupal core ships the optional **Content
Moderation** module (built on the **Workflows** module), which adds a
richer state machine on top of that binary status. Its default "Editorial"
workflow defines three states — **Draft**, **Published**, **Archived** —
and lets you "have a published version that is live, but have a separate
working copy that is undergoing review before it is published." It
explicitly "expand[s] on Drupal's 'unpublished' and 'published' states"
with custom states/transitions (Create New Draft, Publish, Archive, Restore
to Draft, Restore).
Source: [Content Moderation module overview](https://www.drupal.org/docs/8/core/modules/content-moderation/overview) (drupal.org).

**Roles vs. permissions.** Drupal's docs define the terms directly:
"Anyone who visits your website is a user, including you" — anonymous
(not logged in), authenticated (logged in), and User 1 (the admin account
made at install). A **permission** "govern[s] the ability to do actions on
your site (including viewing content, editing content, and changing
configuration)"; each permission covers one action or a small subset.
Rather than granting permissions per user, "permissions are grouped into
**roles**" — a user gets every permission attached to each role assigned to
them. Built-in roles: **Authenticated user** (auto-assigned to every
account) and **Anonymous user** (assigned to logged-out visitors); many
installs also configure an **Administrator** role with all permissions.
Source: [7.1 Concept: Users, Roles, and Permissions](https://www.drupal.org/docs/user_guide/en/user-concept.html) (drupal.org User Guide).

Permissions are fine-grained and often per-content-type: the admin UI
(People > Roles > Edit permissions) lists items like "Recipe: Create new
content," "Recipe: Edit own content," "Recipe: Delete own content" —
distinguishing "own" from "any" content, and permissions available depend on
which modules are installed.
Source: [7.5 Assigning Permissions to a Role](https://www.drupal.org/docs/user_guide/en/user-permissions.html) (drupal.org User Guide).

**Publishing model.** Like WordPress, Drupal is database-backed with no
build step: "publish" is a status/state transition (Published checkbox, or
a Content Moderation state) that a live PHP request evaluates against the
viewer's permissions on every page load. The Content Moderation module adds
the concept of keeping a live published revision and a separate in-review
draft revision of the *same* entity simultaneously, which WordPress's
simpler status model doesn't natively do.

---

## Static-site generators (Jekyll, Hugo)

Static-site generators have **no server-side database and no live admin
UI** — content lives as files in the repo, and "publishing" is a
**build-time** decision (what gets included when the generator turns source
files into static HTML), not a runtime status check.

**Content type.** Hugo's own glossary defines it precisely: a content type
is "a classification of content inferred from the top-level directory name
or the `type` set in front matter," which drives template lookup and which
archetype is used for new content — i.e., directory structure (or explicit
front matter) *is* the content-type system, not a database column.
Source: [Hugo Glossary](https://gohugo.io/getting-started/glossary/) (gohugo.io).
Jekyll has a looser notion: **posts** are files in `_posts/` following the
filename convention `YEAR-MONTH-DAY-title.MARKUP`; **pages** are any other
processed file; **collections** (a more general Jekyll feature) group
arbitrary custom content types beyond posts/pages.
Source: [Jekyll: Posts](https://jekyllrb.com/docs/posts/) (jekyllrb.com).

**Front matter.** Both tools use the same term for embedded metadata. Hugo:
"the metadata at the beginning of each content page, separated from the
content by format-specific delimiters."
Source: [Hugo Glossary](https://gohugo.io/getting-started/glossary/) (gohugo.io).
Jekyll: "Any file that contains a YAML front matter block will be processed
by Jekyll as a special file... The front matter must be the first thing in
the file and must take the form of valid YAML set between triple-dashed
lines."
Source: [Jekyll: Front Matter](https://jekyllrb.com/docs/front-matter/) (jekyllrb.com).

**Draft/published without a database.** Both tools push this decision into
the build step, using the filesystem itself as the state:
- **Jekyll drafts**: posts *without* a date in the filename, stored in
  `_drafts/`. A normal `jekyll build`/`jekyll serve` skips them entirely;
  running with `--drafts` includes them, using the file's modification
  time as its date.
  Source: [Jekyll: Posts](https://jekyllrb.com/docs/posts/) (jekyllrb.com).
- **Jekyll `published: false`**: a front-matter flag on any post — "Set to
  false if you don't want a specific post to show up when the site is
  generated" — overridable at build time with the `--unpublished` switch.
  Source: [Jekyll: Front Matter](https://jekyllrb.com/docs/front-matter/) (jekyllrb.com).
- Hugo has an analogous pattern (`draft: true` front matter excluded from
  a normal `hugo` build, included with `--buildDrafts`), consistent with
  its glossary's framing of a **build** as the act of "generat[ing] the
  static files for a project ... resolving the matrix of language, role,
  and version defined in your project configuration" — i.e., inclusion
  rules are evaluated once, at build time, not per-request.
  Source: [Hugo Glossary](https://gohugo.io/getting-started/glossary/) (gohugo.io).

**Slug / permalink / section / taxonomy / theme (Hugo glossary terms).**
- **Section**: "A top-level content directory or any content directory
  containing an `_index.md` file" — determined by directory placement,
  not overridable in front matter.
- **Slug**: the final URL path segment, optionally overridden in front
  matter (per Hugo's content organization docs).
- **Permalink**: "The absolute URL of a published resource or a rendered
  page, including scheme and host."
- **Taxonomy**: "A group of related terms used to classify content. For
  example, a `colors` taxonomy might include the terms `red`, `green`, and
  `blue`" — same term/taxonomy relationship as WordPress, but purely a
  build-time content-indexing feature, no DB table.
- **Theme**: "A module that delivers a complete set of components defining
  a site's layout, presentation, and behavior. While every theme is a
  module, not every module is a theme."
Source for all five: [Hugo Glossary](https://gohugo.io/getting-started/glossary/) and
[Hugo: Content Organization](https://gohugo.io/content-management/organization/) (gohugo.io).

**No roles/users at all.** Neither Jekyll nor Hugo has a concept of a
logged-in user, role, or capability — there's no runtime to log into. Access
control (who can *edit* the source repo) is pushed entirely outside the
tool, onto the hosting/version-control layer (e.g., GitHub repo
collaborators/branch protection), which is exactly the gap our FastAPI admin
console is filling for our own project: we need the runtime editor +
role/capability layer that Jekyll/Hugo deliberately don't have, while still
publishing to static HTML like they do.

**"Publish" reframed.** For WordPress/Drupal, publish = a status flip a live
server evaluates on each request (runtime, reversible, instant). For
Jekyll/Hugo, "publish" = whichever files/front-matter flags are included in
the *next build run*, then pushed/deployed as static output — there is no
"live database" to flip a flag in; the generated HTML on disk (or on
GitHub Pages) simply doesn't contain draft content until a build says so.
This is the direct model for our own project: SQLite is the "draft
database" equivalent of Jekyll's `_drafts/`, and our render-to-static-HTML
step is the "build."

---

## Glossary

| Term | Definition | Used by |
|---|---|---|
| Content type | A named category of content with its own set of fields/structure (post type in WP, content type/bundle in Drupal, inferred-from-directory or `type` front matter in Hugo) | WordPress, Drupal, Hugo |
| Post type | WordPress's term for content type; all post types share one `posts` DB table | WordPress |
| Entity | Drupal's most general unit of content data (text, HTML, files, etc.) | Drupal |
| Bundle / entity subtype | A named variant of an entity type with its own fields (a Drupal content type is a bundle of the "Content item" entity type) | Drupal |
| Field | A single typed piece of data stored on an entity/post (text, image, date, etc.) | WordPress, Drupal |
| Slug | The URL-safe identifier for a piece of content, usually derived from its title | WordPress, Hugo |
| Permalink | The full, stable URL at which a published item is reachable | WordPress, Hugo |
| Post status | A string field marking a post's lifecycle state (`draft`, `pending`, `future`, `publish`, `private`, etc.) | WordPress |
| Draft | Content saved but not publicly visible; in SSGs, expressed as `_drafts/` file location or a `published`/`draft` front-matter flag rather than a DB row | WordPress, Drupal, Jekyll, Hugo |
| Published | Content visible to the public — a live status flip (WP/Drupal) or files included in the last build (Jekyll/Hugo) | WordPress, Drupal, Jekyll, Hugo |
| Scheduled | A post set to auto-publish at a future date/time (`future` status in WordPress) | WordPress |
| Content moderation / workflow state | A richer state machine (e.g. Draft/Published/Archived) layered on top of basic published/unpublished, with defined transitions | Drupal (Content Moderation module) |
| Role | A named bundle of capabilities/permissions assigned to a user | WordPress, Drupal |
| Capability | A single named permission-to-do-a-specific-thing (WordPress term); e.g. `publish_posts`, `edit_others_posts` | WordPress |
| Permission | A single named permission-to-do-a-specific-thing (Drupal term); often scoped per content type and per "own" vs. "any" | Drupal |
| Taxonomy | A classification system grouping content via named terms (e.g. category, tag) | WordPress, Hugo |
| Term | An individual value within a taxonomy (e.g. "Modern" within an "Art" taxonomy) | WordPress, Hugo |
| Theme | The presentation/template layer that renders stored content, kept separate from the content itself | WordPress, Hugo |
| Headless | Using the CMS purely as a content API/store, with rendering done by a separate front-end application | WordPress (via REST API) |
| Front matter | A YAML (or similar) metadata block at the top of a content file | Jekyll, Hugo |
| Section | A top-level (or `_index.md`-marked) content directory that groups related content in an SSG | Hugo |
| Build | The generation step that turns source files/front matter into static output files, applying inclusion rules (e.g. draft exclusion) at that point rather than per-request | Jekyll, Hugo |
| Static site | Pre-rendered HTML files served as-is, with no live database or server-side runtime consulted per request | Jekyll, Hugo (and our own project's output) |

---

## Sources consulted

- [developer.wordpress.org — Post Types](https://developer.wordpress.org/plugins/post-types/)
- [developer.wordpress.org — `get_post_status()`](https://developer.wordpress.org/reference/functions/get_post_status/)
- [developer.wordpress.org — Taxonomies](https://developer.wordpress.org/plugins/taxonomies/)
- [developer.wordpress.org — Roles and Capabilities](https://developer.wordpress.org/plugins/users/roles-and-capabilities/)
- [developer.wordpress.org — What is a Theme?](https://developer.wordpress.org/themes/getting-started/what-is-a-theme/)
- [developer.wordpress.org — REST API Handbook](https://developer.wordpress.org/rest-api/)
- [drupal.org — 2.4 Planning Content Types](https://www.drupal.org/docs/user_guide/en/planning-data-types.html)
- [drupal.org — 2.5 Planning your Content Structure / Publishing Options](https://www.drupal.org/docs/user_guide/en/planning-structure.html)
- [drupal.org — Content Moderation module overview](https://www.drupal.org/docs/8/core/modules/content-moderation/overview)
- [drupal.org — 7.1 Concept: Users, Roles, and Permissions](https://www.drupal.org/docs/user_guide/en/user-concept.html)
- [drupal.org — 7.5 Assigning Permissions to a Role](https://www.drupal.org/docs/user_guide/en/user-permissions.html)
- [jekyllrb.com — Posts](https://jekyllrb.com/docs/posts/)
- [jekyllrb.com — Front Matter](https://jekyllrb.com/docs/front-matter/)
- [gohugo.io — Glossary](https://gohugo.io/getting-started/glossary/)
- [gohugo.io — Content Organization](https://gohugo.io/content-management/organization/)
