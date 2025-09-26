import React, { useState } from "react";

// Image assets exported from Figma MCP server (placeholder URLs)
const imgSendArrow = "http://localhost:3845/assets/9d49f9e4e3d972e5fe99de585fd9952ac6047207.svg"; // send
const imgAttachmentIcon = "http://localhost:3845/assets/0b2ce89b2b52f214d51d2a684c096c01c0dcb9ed.svg"; // attach
const imgDeepResearch = "http://localhost:3845/assets/e99107f05c11f364d438e580ffc8e2defe2380e4.svg"; // deep research
const imgRag = "http://localhost:3845/assets/e9472ded5057bf6576eec32fd660ceff9b70d10b.svg"; // rag
const imgWhisper = "http://localhost:3845/assets/8e40df5e274cb8bba22508714ec5a8c3aaed2700.svg"; // whisper
const imgGroup = "http://localhost:3845/assets/2f1a55905e4105254854e081ffd477309c5adfc6.svg"; // history / expand

type ToolKey = 'deep' | 'rag' | 'whisper';

export const ChatInterface: React.FC<{ onToggleTheme?: () => void; isDarkMode?: boolean }> = ({ onToggleTheme, isDarkMode }) => {
	const [activeTool, setActiveTool] = useState<ToolKey>('rag');
	const bg = isDarkMode ? '#1b1b1b' : '#f5f5f5';
	const surface = isDarkMode ? '#2e2e2e' : '#ffffff';
	const subtle = isDarkMode ? 'border-white/10' : 'border-black/10';
	const textMuted = isDarkMode ? 'text-gray-400' : 'text-gray-500';

	const toolDefs: { key: ToolKey; label: string; icon: string }[] = [
		{ key: 'deep', label: 'Deep Research', icon: imgDeepResearch },
		{ key: 'rag', label: 'RAG', icon: imgRag },
		{ key: 'whisper', label: 'Whisper', icon: imgWhisper },
	];

	return (
		<div className="flex flex-col h-screen w-full" style={{ backgroundColor: bg }}>
			{/* Scrollable messages area (placeholder) */}
			<div className="flex-1 overflow-y-auto px-4 pt-4 pb-28 md:pb-36 space-y-4">
				{/* Placeholder empty state */}
				<div className="h-full w-full flex items-center justify-center pointer-events-none select-none">
					<div className="text-center max-w-xs">
						<h2 className="text-sm font-semibold tracking-wide text-gray-200">JD Copilot</h2>
						<p className={`${textMuted} mt-2 text-xs leading-relaxed`}>Start by typing a prompt or pick a tool below.</p>
					</div>
				</div>
			</div>

			{/* Bottom composer & toolbox wrapper */}
			<div className="pointer-events-auto fixed left-0 right-0 bottom-0 px-4 pb-4 pt-2 md:px-6" style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.55), rgba(0,0,0,0))' }}>
				{/* Composer */}
				<div
					className={`relative rounded-lg border ${subtle} shadow-[0_4px_12px_-2px_rgba(0,0,0,0.35)] px-3 pt-3 pb-2 flex items-end gap-2`}
					style={{ backgroundColor: surface }}
				>
					{/* Attachment */}
						<button
						type="button"
						aria-label="Attach file"
						className="shrink-0 p-1.5 rounded-md hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
					>
						<img src={imgAttachmentIcon} alt="attach" className="w-4 h-4 opacity-80" />
					</button>

					{/* Textarea */}
					<textarea
						rows={1}
						placeholder="Alright genius, spit out..."
						className={`flex-1 resize-none bg-transparent outline-none text-sm leading-relaxed placeholder:${textMuted} text-gray-100 max-h-40 min-h-[24px]`}
					/>

					{/* Send */}
					<button
						type="button"
						aria-label="Send"
						className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center hover:brightness-110 active:scale-95 transition shadow-md"
					>
						<img src={imgSendArrow} alt="send" className="w-4 h-4" />
					</button>
				</div>

				{/* Toolbox row */}
				<div className="mt-3 flex items-center justify-center gap-3 relative">
					<div className="flex items-center gap-2 px-3 py-2 rounded-xl backdrop-blur-sm bg-black/40 border border-white/10 shadow-[0_0_8px_-2px_rgba(0,0,0,0.5)]">
						{toolDefs.map(t => {
							const active = t.key === activeTool;
							return (
								<button
									key={t.key}
									type="button"
									onClick={() => setActiveTool(t.key)}
									className={`relative w-11 h-11 rounded-md flex items-center justify-center transition outline-none focus:ring-2 focus:ring-orange-400/60 ${active ? 'bg-[#272321] ring-1 ring-orange-400 shadow-[0_0_0_1px_rgba(255,138,76,0.35)]' : 'bg-white/5 hover:bg-white/10'} `}
									aria-pressed={active}
									aria-label={t.label}
								>
									<img src={t.icon} alt={t.label} className={`w-6 h-6 ${active ? 'brightness-110 saturate-150' : 'opacity-80'}`} />
									{active && (
										<span className="absolute -bottom-1 left-1/2 -translate-x-1/2 h-1.5 w-1.5 rounded-full bg-orange-400" />
									)}
								</button>
							);
						})}
					</div>

					{/* History / expand button */}
					<button
						type="button"
						onClick={() => onToggleTheme && onToggleTheme()}
						className="absolute right-0 translate-x-[115%] w-12 h-12 rounded-md flex items-center justify-center bg-black/40 border border-white/10 hover:bg-black/60 transition outline-none focus:ring-2 focus:ring-blue-500/60"
						aria-label="Toggle theme / history"
					>
						<img src={imgGroup} alt="history" className="w-6 h-6 opacity-80" />
					</button>
				</div>
				<div className="h-safe" />
			</div>
		</div>
	);
};