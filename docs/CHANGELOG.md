# Changelog

## [WHITE1.1] - November 3, 2025

### Added - Junk & Attention Management
- 🗑️ **Junk Management System**
  - Mark emails as junk with fade-out animation
  - Dedicated Junk view (4th button)
  - Restore functionality with ↩️ button
  - Database persistence with `is_junk` column
  
- ⚠️ **Attention Flagging**
  - Mark emails for attention with visual highlighting
  - Orange left border + bold title styling
  - Toggle on/off functionality
  - Database persistence with `is_attention` column

- 📊 **4-View System**
  - Hybrid view (all non-junk)
  - News Flow (NewsBreif stories)
  - Analysis (deep analysis items)
  - Junk (junked emails only)

- 🔌 **New API Endpoints**
  - `POST /api/mark_junk/<id>`
  - `POST /api/unmark_junk/<id>`
  - `POST /api/toggle_attention/<id>`
  - `GET /api/feed?view=junk`

### Fixed
- Gmail list button onclick handlers using proper closures
- API filtering order (filter after loading data)
- Header preservation in Junk view
- `is_junk` and `is_attention` fields in API responses

### Technical
- Switched to `createElement` for dynamic buttons
- Proper function closures for event handlers
- Smart view-based filtering
- Enhanced CSS for attention styling

---

## [WHITE1.0] - November 2, 2025
- Initial release with NewsBreif story splitting
- Smart link extraction
- Keyword extraction
- Admin interface (port 8543)

