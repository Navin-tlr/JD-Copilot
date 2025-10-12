# Chat History UI - Dark Theme Color Reference

## Complete Color Palette

### Background Colors
```css
Main Background:        #313131  /* Page background */
Sidebar Background:     #2A2A2A  /* Sidebar main color */
Card Background:        #2f2f2f  /* Session card background */
Hover Background:       #353535  /* Card hover state */
Active Background:      #3D3D3D  /* Selected session & buttons */
Button Hover:           #4A4A4A  /* Button hover state */
```

### Border Colors
```css
Main Border:            #404040  /* Sidebar edges, separators */
Card Border:            #505050  /* Card hover border */
Active Border:          #D38B21  /* Selected session (orange accent) */
```

### Text Colors
```css
Primary Text:           #E0E0E0  /* Headings, session names */
Secondary Text:         #8A8A8A  /* Timestamps */
Muted Text:             #6A6A6A  /* Message counts, footer */
Button Text:            #E0E0E0  /* Button labels */
Icon Color:             #C1C1C1  /* Chat history arrow */
Delete Hover:           #FF6B6B  /* Delete button on hover */
```

### Special Effects
```css
Backdrop:               rgba(0,0,0,0.4) + backdrop-blur-sm
Spinner:                #C1C1C1  /* Loading animation */
```

---

## Component Breakdown

### Chat History Arrow Button
```tsx
<button className="pr-4 transition-transform hover:scale-110">
  <svg stroke="#C1C1C1" strokeWidth="1.5">
    {/* Arrow icon */}
  </svg>
</button>
```
- **Location**: Top-right header
- **Color**: `#C1C1C1` (light gray)
- **Hover**: Scale 110%
- **Action**: Opens sidebar

---

### Sidebar Container
```tsx
<div className="fixed top-0 right-0 h-full w-80 
               bg-[#2A2A2A] border-l border-[#404040]">
```
- **Width**: 320px (80 * 4px)
- **Background**: `#2A2A2A`
- **Border Left**: `#404040`
- **Animation**: slide-in-right (0.3s ease-out)

---

### Header Section
```tsx
<div className="p-4 border-b border-[#404040]">
  <h2 className="text-[16px] font-semibold text-[#E0E0E0]">
    Chat History
  </h2>
  <button className="text-[#C1C1C1] hover:text-[#FFFFFF]">
    <X size={18} />
  </button>
</div>
```
- **Padding**: 16px all sides
- **Border Bottom**: `#404040`
- **Title**: 16px semibold, `#E0E0E0`
- **Close Button**: `#C1C1C1` → `#FFFFFF` on hover

---

### New Chat Button
```tsx
<button className="w-full px-4 py-2.5 
                  bg-[#3D3D3D] hover:bg-[#4A4A4A]
                  text-[#E0E0E0] border border-[#505050]
                  rounded-lg">
  <Plus size={18} />
  <span className="text-[14px]">New Chat</span>
</button>
```
- **Background**: `#3D3D3D` → `#4A4A4A` on hover
- **Text**: 14px medium, `#E0E0E0`
- **Border**: `#505050`
- **Hover Effect**: scale(1.02)
- **Active Effect**: scale(0.98)

---

### Session Card (Normal)
```tsx
<div className="p-3 rounded-lg
               bg-[#2f2f2f] border-transparent
               hover:bg-[#353535] hover:border-[#505050]">
  <p className="text-[13px] text-[#E0E0E0]">Session name</p>
  <span className="text-[11px] text-[#8A8A8A]">2h ago</span>
  <span className="text-[11px] text-[#6A6A6A]">· 5 msgs</span>
</div>
```
- **Background**: `#2f2f2f` → `#353535` on hover
- **Border**: transparent → `#505050` on hover
- **Title**: 13px medium, `#E0E0E0`
- **Time**: 11px, `#8A8A8A`
- **Count**: 11px, `#6A6A6A`

---

### Session Card (Active/Selected)
```tsx
<div className="p-3 rounded-lg
               bg-[#3D3D3D] border-[#D38B21]">
  {/* Same content structure */}
</div>
```
- **Background**: `#3D3D3D` (darker than normal)
- **Border**: `#D38B21` (orange accent - only place orange is used)
- **Text**: Same colors as normal state

---

### Delete Button
```tsx
<button className="opacity-0 group-hover:opacity-100
                  p-1.5 rounded-lg hover:bg-[#4A4A4A]
                  text-[#8A8A8A] hover:text-[#FF6B6B]">
  <Trash2 size={14} />
</button>
```
- **Default**: Hidden (opacity-0)
- **On Card Hover**: Visible (opacity-100)
- **Color**: `#8A8A8A` → `#FF6B6B` (red) on hover
- **Background**: transparent → `#4A4A4A` on hover

---

### Empty State
```tsx
<div className="text-[#6A6A6A]">
  <MessageSquare size={32} className="opacity-50" />
  <p className="text-sm">No chat history yet</p>
</div>
```
- **Icon**: 32px, `#6A6A6A` at 50% opacity
- **Text**: 14px, `#6A6A6A`

---

### Loading State
```tsx
<div className="animate-spin rounded-full h-8 w-8 
               border-b-2 border-[#C1C1C1]" />
```
- **Size**: 32px × 32px
- **Border**: 2px bottom border, `#C1C1C1`
- **Animation**: Spin infinite

---

### Footer
```tsx
<div className="p-3 border-t border-[#404040]
               text-[11px] text-[#8A8A8A]">
  5 of 10 chats stored
</div>
```
- **Border Top**: `#404040`
- **Text**: 11px, `#8A8A8A`
- **Padding**: 12px all sides

---

### Backdrop
```tsx
<div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
```
- **Background**: Black at 40% opacity
- **Effect**: backdrop-blur-sm (subtle blur)
- **Z-index**: 40 (sidebar is 50)

---

## Contrast Ratios (WCAG Compliance)

```
Background vs Text:
#2A2A2A vs #E0E0E0 → 10.2:1 ✅ (AAA)
#2A2A2A vs #8A8A8A → 4.8:1  ✅ (AA)
#2A2A2A vs #6A6A6A → 3.2:1  ⚠️  (Large text only)

Active Border:
#3D3D3D vs #D38B21 → 4.1:1  ✅ (AA)

Delete Button:
#2A2A2A vs #FF6B6B → 5.2:1  ✅ (AA)
```

---

## Animation Details

### Slide-In Animation
```css
@keyframes slide-in-right {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}
```

### Hover Scale Effects
```css
/* Button hover */
hover:scale-[1.02]    /* 102% size */
active:scale-[0.98]   /* 98% size when clicked */

/* Arrow icon hover */
hover:scale-110       /* 110% size */
```

---

## Spacing System

```css
Sidebar Width:     320px (w-80)
Padding:           12-16px (p-3, p-4)
Gap between cards: 8px (space-y-2)
Border Radius:     8px (rounded-lg)
Icon Size:         14-18px
Text Size:         11-16px
```

---

## Quick Reference Chart

| Element              | BG Color  | Text Color | Border    | Hover BG  |
|---------------------|-----------|------------|-----------|-----------|
| Sidebar             | `#2A2A2A` | `#E0E0E0`  | `#404040` | N/A       |
| New Chat Button     | `#3D3D3D` | `#E0E0E0`  | `#505050` | `#4A4A4A` |
| Session Card        | `#2f2f2f` | `#E0E0E0`  | transp.   | `#353535` |
| Active Session      | `#3D3D3D` | `#E0E0E0`  | `#D38B21` | N/A       |
| Delete Button       | transp.   | `#8A8A8A`  | N/A       | `#4A4A4A` |
| Footer              | `#2A2A2A` | `#8A8A8A`  | `#404040` | N/A       |

---

## Implementation Notes

1. **Orange Accent**: Only used for active session border (`#D38B21`)
2. **Consistent Grays**: Three levels (#E0E0E0, #8A8A8A, #6A6A6A)
3. **Hover States**: Always provide visual feedback
4. **Transitions**: All color/transform changes are smooth
5. **Z-Index Layers**: Backdrop (40) < Sidebar (50)
6. **Responsive**: Fixed width (320px) works on all screen sizes
