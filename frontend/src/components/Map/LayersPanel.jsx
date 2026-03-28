function LayersPanel({ layers, onToggleLayer, onClose }) {
  return (
    <div className="absolute top-4 right-4 z-[1000] w-72 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-sky-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-sky-100">
        <h3 className="text-sm font-bold text-sky-900">שכבות</h3>
        <button
          onClick={onClose}
          className="text-sky-300 hover:text-sky-600 text-lg leading-none"
        >
          &times;
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-sky-100">
        <button className="flex-1 px-4 py-2 text-sm font-medium text-sky-600 border-b-2 border-sky-500">
          בחירת שכבות
        </button>
      </div>

      {/* Layers List */}
      <div className="p-4 flex flex-col gap-3">
        {layers.map((layer) => (
          <label
            key={layer.id}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <input
              type="checkbox"
              checked={layer.visible}
              onChange={() => onToggleLayer(layer.id)}
              className="w-4 h-4 text-sky-500 rounded border-sky-300
                         focus:ring-sky-400 cursor-pointer"
            />
            <div className="flex flex-col">
              <span className="text-sm text-sky-800 group-hover:text-sky-900">
                {layer.name}
              </span>
              {layer.description && (
                <span className="text-xs text-sky-400">
                  {layer.description}
                </span>
              )}
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}

export default LayersPanel
