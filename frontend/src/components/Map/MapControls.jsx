const BTN_BASE = `w-10 h-10 rounded-xl shadow-md border
                  flex items-center justify-center transition-all duration-200`

const BTN_DEFAULT = `${BTN_BASE} bg-white/90 backdrop-blur-sm border-sky-200 text-sky-700 hover:bg-sky-50 hover:border-sky-300`
const BTN_ACTIVE = `${BTN_BASE} bg-sky-500 text-white border-sky-500 shadow-sky-200`
const BTN_DISABLED = `disabled:opacity-40 disabled:cursor-not-allowed`

function MapControls({ zoom, minZoom, maxZoom, onZoomIn, onZoomOut, onLocate, onResetView, onToggleLayers, isLayersPanelOpen, onToggleSearch, isSearchOpen, onToggleDbLayers, isDbLayersOpen }) {
  return (
    <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-2">
      {/* Layers Toggle */}
      <button
        onClick={onToggleLayers}
        className={isLayersPanelOpen ? BTN_ACTIVE : BTN_DEFAULT}
        title="שכבות"
      >
        &#9776;
      </button>

      {/* Search Toggle */}
      <button
        onClick={onToggleSearch}
        className={isSearchOpen ? BTN_ACTIVE : BTN_DEFAULT}
        title="חיפוש"
      >
        &#128269;
      </button>

      {/* Database Layers Toggle */}
      <button
        onClick={onToggleDbLayers}
        className={isDbLayersOpen ? BTN_ACTIVE : BTN_DEFAULT}
        title="בסיסי נתונים"
      >
        &#128202;
      </button>

      <div className="h-1" />

      {/* Zoom In */}
      <button
        onClick={onZoomIn}
        disabled={zoom >= maxZoom}
        className={`${BTN_DEFAULT} ${BTN_DISABLED} text-xl font-bold`}
        title="הגדל"
      >
        +
      </button>

      {/* Zoom Out */}
      <button
        onClick={onZoomOut}
        disabled={zoom <= minZoom}
        className={`${BTN_DEFAULT} ${BTN_DISABLED} text-xl font-bold`}
        title="הקטן"
      >
        −
      </button>

      {/* Locate Me */}
      <button onClick={onLocate} className={`${BTN_DEFAULT} text-lg`} title="המיקום שלי">
        &#8982;
      </button>

      {/* Reset View */}
      <button onClick={onResetView} className={`${BTN_DEFAULT} text-lg`} title="תצוגת ישראל">
        &#8634;
      </button>

      {/* Zoom Level Indicator */}
      <div className="w-10 h-8 bg-white/70 backdrop-blur-sm rounded-xl shadow-md border border-sky-100
                       flex items-center justify-center text-xs text-sky-400 font-medium">
        {zoom}
      </div>
    </div>
  )
}

export default MapControls
