# RAG Mode UI - Figma Alignment Summary

## Quick Reference Guide

### Component Positions (Based on Figma Design)

```
RAG MODE SCREEN (1280 x 832)
│
├── Header Section (y: 46)
│   ├── Sapient Logo (x: 38, y: 46)
│   └── Chat History Arrow (x: 1214, y: 51)
│
├── Content Area (Centered)
│   ├── RAG Icon (x: 555, y: 214) [155x155px]
│   │   └── Gap: 47px
│   └── RAG FX Description (x: 516, y: 416) [247x75px]
│       ├── Code Icon (w: 13px, h: 8px)
│       └── Text (font: Hack, size: 11px, line-height: 15px)
│
└── Chat Component (x: 176, y: 665) [914x116px]
    ├── Attachment Icon (x: 20, y: 15) [21x21px]
    ├── Input Field (x: 60, y: 17)
    ├── Tool Box (x: 20, y: 63) [155x40px]
    │   ├── Deep Research Button (x: 8, disabled)
    │   ├── RAG Button (x: 55) [38x31px] - ACTIVE: #D38B21
    │   └── Whisper Button (x: 104, disabled)
    ├── RAG Mode Indicator (x: 186, y: 72) [26x26px]
    └── Send Arrow (x: 873, y: 76) [23x23px]
```

## Color Palette

### Main Colors
- **Background:** `#313131` (Dark Gray)
- **Chat Component:** `#464646` (Medium Gray)
- **Tool Box:** `#393939` (Slightly Darker Gray)
- **Tool Items:** `#4A4A4A` (Button Gray)

### Active States
- **RAG Active BG:** `#D38B21` (Orange)
- **RAG Active Stroke:** `#464646` (Match Chat BG)
- **Send Active:** `rgb(246,159,28)` (Bright Orange)

### Text Colors
- **Primary Text:** `#FFFFFF` (White)
- **Description Text:** `#D7D2CF` (Light Beige)
- **Icons:** `#C1C1C1` (Light Gray)
- **Placeholder:** `rgba(255, 255, 255, 0.6)` (60% White)

### Gradients (RAG Icon)
- **Gradient Start:** `#C8C6C4` (Light Gray)
- **Gradient End:** `#7F7B79` (Dark Gray)

## Typography Specs

### Hack Font Family
```css
font-family: 'Hack', monospace;
```

### Text Specifications
- **Description:** 11px / 15px (size / line-height)
- **Input Placeholder:** 14px
- **Font Weights:** 400 (Regular), 700 (Bold)

## Key Measurements

### Spacing
- **Icon to Description Gap:** 47px
- **Tool Box Height:** 40px
- **Tool Button Size:** 38x31px
- **Tool Box Gap:** 1px (gap-1)
- **Padding Around Tool Buttons:** 8px

### Component Dimensions
- **Max Container Width:** 1280px
- **Chat Component Width:** 914px
- **Chat Component Height:** 116px
- **RAG Icon:** 155x155px
- **Description Max Width:** 247px

## Alignment Rules

1. **Vertical Centering:**
   - Use `items-center` for perfect vertical alignment
   - Content area uses `flex-1` to fill available space

2. **Horizontal Centering:**
   - Max width container: `max-w-[1280px]`
   - Chat input: `max-w-[914px]`
   - Center with `mx-auto` or `justify-center`

3. **Absolute Positioning:**
   - All fixed elements use absolute positioning within Chat Component
   - Positions are exact pixel values from Figma

## States & Interactions

### RAG Button States
```
Normal: 
  - Background: #4A4A4A
  - Icon: Orange gradient

Active (on /rag route):
  - Background: #D38B21
  - Icon: #464646 (solid)
```

### Send Arrow States
```
Inactive:
  - Stroke: #B5B5B5 (87% opacity)
  - Cursor: default

Active (with input):
  - Stroke: rgb(246,159,28)
  - Cursor: pointer
  - Hover: Translate up + shadow glow
```

## Implementation Notes

### Critical Alignments Fixed
1. ✅ RAG icon and description spacing: 47px (was 32px)
2. ✅ Send arrow size: 23x23px (was 25x25px)
3. ✅ Vertical centering: Added `items-center`
4. ✅ Text line-height: 15px for description
5. ✅ Paragraph margin: `mb-0` to remove default spacing

### Already Correct
- Tool box positioning at x:20, y:63
- RAG button active color (#D38B21)
- Icon gradients and colors
- Font family (Hack) configuration
- Input field placeholder styling

## Testing Checklist

- [ ] RAG icon appears centered horizontally and vertically
- [ ] Description text is 47px below the RAG icon
- [ ] Send arrow is exactly 23x23px
- [ ] RAG button shows orange (#D38B21) on /rag route
- [ ] Hover effects work on send arrow (translate up + glow)
- [ ] All colors match Figma specifications
- [ ] Hack font renders correctly
- [ ] Active states trigger properly
- [ ] Responsive behavior maintains alignment

## Files Modified

1. `/client/pages/RAGMode.tsx`
   - Updated gap from `gap-8` to `gap-[47px]`
   - Added `items-center` for proper centering
   - Added `mb-0` to description paragraph

2. `/client/components/ChatInput.tsx`
   - Updated send arrow SVG from 25x25 to 23x23px
   - Verified all positioning values match Figma

## Figma Reference
- Node ID: 93:101 (RAG MODE screen)
- Chat Component: 93:102
- RAG Icon: 93:158
- RAG FX Description: 93:167
