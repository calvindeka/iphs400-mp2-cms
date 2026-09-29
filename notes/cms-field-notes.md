# Field notes

(Part 2 of the manual: at least five things you noticed inside WordPress Playground, in your own words.)

1. **A draft really is invisible.** I wrote a post ("Fall Meeting Reminder"), saved it as a draft, and checked the public blog page in the same tab — it wasn't there, just the default "Hello world!" post. Only after clicking Publish did it show up. Nothing about the editor UI makes that obvious; you have to actually go check the front end to believe it.

2. **The slug writes itself as you type the title.** The moment I typed "Fall Meeting Reminder" into the title field, the sidebar's Slug field filled in as `fall-meeting-reminder` with no extra step. I hadn't touched Permalinks yet — it just happens on every post/page as you type.

3. **Pages and posts are genuinely different kinds of content, not just a label.** A published page ("About") showed up immediately in the site's top navigation menu, next to "Sample Page." A published post never did — it only ever appeared in the Blog feed. Same editor, same buttons, completely different destination.

4. **An editor's admin sidebar is just missing the admin-only items, not greyed out.** Logged in as an Editor-role test account, the left sidebar had no Appearance, Plugins, Users, or Settings links at all — they weren't disabled, they were absent, as if they didn't exist for that account.

5. **Access control is enforced on the URL, not just hidden in the menu.** I typed `/wp-admin/users.php` directly into the address bar while logged in as the editor account (bypassing the missing sidebar link entirely). WordPress didn't just redirect — it showed "You need a higher level of permission. Sorry, you are not allowed to list users." That's a real server-side check, not UI hiding.

6. **The post list is the filterable content list the lab describes.** "All Posts" has tabs across the top (All / Published / Draft, depending what exists) plus dropdown filters for date and category — this is clearly the same screen our CMS's admin console list/filter requirement (rubric C5) is modeled on.

7. **Concurrent editing has its own indicator.** While the admin account still had the post open in the editor, the editor account's post list showed a small lock icon and "admin is currently editing" next to that post's title instead of a normal link. I wasn't expecting WordPress to track that.
