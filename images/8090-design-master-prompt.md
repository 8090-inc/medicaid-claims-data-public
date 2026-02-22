# 8090 DESIGN MASTER PROMPT

> **Design System**: Industrial Blueprint Editorial × Tailwind Slate × shadcn/ui Nova
> **Use this prompt** as the foundation for every 8090 prototype. Paste it at the start of any vibe-coding session.

---

## STEP 1: Apply the 8090 Design System

### COLORS

| Role | Tailwind Token | Hex | Usage |
|------|---------------|-----|-------|
| **Primary Accent** | `brand-blue` (custom) | `#0052CC` | ONE accent element per panel (Factory Blue) |
| **Background** | `bg-slate-50` | `#f8fafc` | Page canvas — replaces Draft Paper Cream |
| **Surface / Cards** | `bg-white` or `bg-slate-100` | `#ffffff` / `#f1f5f9` | Card panels, containers |
| **Border / Dividers** | `border-slate-200` | `#e2e8f0` | Panel edges, separators, hairlines |
| **Secondary Text** | `text-slate-500` | `#64748b` | Captions, metadata, supporting copy |
| **Body Text** | `text-slate-700` | `#334155` | Paragraphs, descriptions |
| **Headlines** | `text-slate-950` | `#020617` | All headings, titles, emphasis |
| **Linework / Shadows** | `text-slate-900` | `#0f172a` | Illustration linework, shadows at 15-30% opacity |
| **Muted / Disabled** | `text-slate-400` | `#94a3b8` | Placeholder text, disabled states |
| **Error** | `text-red-500` | `#ef4444` | Validation errors, destructive actions, system errors |

**COLOR RULES:**
- Use ONLY Factory Blue (`#0052CC`) as the accent color — map it to a custom `brand` token in your Tailwind config
- All neutrals come from Tailwind's **slate** palette (`slate-50` through `slate-950`)
- **All brand color variants are the same hue at different opacities** — no separate hex values, no color-shifted tints
- NO red, yellow, orange, or other accent colors **except** `red-500` (`#ef4444`) for true error states (form validation, destructive actions, system errors)
- NO gradients on UI surfaces
- ONE blue accent element per panel to highlight the key concept

**Brand Color Opacity Scale** (single source of truth: `#0052CC`):

| Token | Class Example | Opacity | Usage |
|-------|--------------|---------|-------|
| `brand` | `bg-brand` / `text-brand` | 100% | Primary buttons, key accent element |
| `brand/80` | `bg-brand/80` | 80% | Hover on primary buttons |
| `brand/60` | `text-brand/60` | 60% | Secondary emphasis, active states |
| `brand/40` | `ring-brand/40` | 40% | Focus rings |
| `brand/20` | `border-brand/20` | 20% | Accent borders, badge outlines |
| `brand/10` | `bg-brand/10` | 10% | Tinted backgrounds, hover surfaces, badges |
| `brand/5` | `bg-brand/5` | 5% | Subtle section highlights |

```js
// tailwind.config.js extension
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: '#0052CC',  // Single value — use Tailwind's /opacity modifier for all variants
      },
    },
  },
}
```

> **Why a single token?** Tailwind's built-in opacity modifier (`bg-brand/10`, `text-brand/40`, etc.) generates every tint you need from one hex value. No secondary tokens, no drift between shades. Every brand surface traces back to `#0052CC`.

**Error State Colors** (using Tailwind's built-in `red` palette):

| Usage | Classes |
|-------|---------|
| Error text | `text-red-500` |
| Error border | `border-red-500` |
| Error background | `bg-red-50` |
| Destructive button | `bg-red-500 hover:bg-red-600 text-white` |
| Destructive button (ghost) | `text-red-500 hover:bg-red-50` |

Red is **only** for functional error communication — form validation messages, destructive action confirmations, and system error banners. Never decorative, never in illustrations.

---

### TYPOGRAPHY

**Primary Font**: `font-sans` → **IBM Plex Sans** with `-1% letter-spacing`
- Load via `@fontsource/ibm-plex-sans` or Google Fonts (`family=IBM+Plex+Sans:wght@400;500;600;700`)
- Fallback stack: `'IBM Plex Sans', ui-sans-serif, system-ui, -apple-system, sans-serif`
- **Global letter-spacing**: Apply `tracking-[-0.01em]` to all `font-sans` text (or set via CSS: `letter-spacing: -0.01em`)

**Monospace Font**: `font-mono` → **Geist Mono** (shadcn Nova default)
- Use for code snippets, data labels, technical callouts
- Fallback stack: `'Geist Mono', ui-monospace, 'Cascadia Code', monospace`

| Element | Class | Size | Weight | Tracking |
|---------|-------|------|--------|----------|
| **Page Title** | `text-4xl sm:text-5xl` | 36–48px | `font-bold` (700) | `tracking-tighter` (-0.05em) |
| **Section Header** | `text-2xl sm:text-3xl` | 24–30px | `font-semibold` (600) | `tracking-tight` (-0.025em) |
| **Panel Title** | `text-lg` | 18px | `font-semibold` (600) | `tracking-[-0.01em]` |
| **Body** | `text-base` | 16px | `font-normal` (400) | `tracking-[-0.01em]` |
| **Caption / Meta** | `text-sm` | 14px | `font-medium` (500) | `tracking-[-0.01em]` |
| **Label / Overline** | `text-xs uppercase` | 12px | `font-semibold` (600) | `tracking-widest` (0.1em) |

> **Note on tracking**: The base `-0.01em` (`-1%`) is the global default for IBM Plex Sans. Headings go tighter. Overlines go wider. Set the base globally so you don't repeat it on every element:
> ```css
> body { font-family: 'IBM Plex Sans', sans-serif; letter-spacing: -0.01em; }
> ```

---

### LAYOUT

**Spacing Scale** (Tailwind 8px base):
- `gap-2` (8px) → tight inner spacing
- `gap-4` (16px) → default component spacing
- `gap-6` (24px) → between related sections
- `gap-8` (32px) → between panels
- `gap-12` (48px) → major section breaks
- `gap-16` (64px) → page-level vertical rhythm

**Grid**:
- Max content width: `max-w-6xl mx-auto` (1152px)
- Panel grid: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8`
- Padding: `px-6 sm:px-8 lg:px-12`

**Rules**:
- Ample whitespace between panels (`gap-8` minimum)
- One illustration per headline
- Clear visual hierarchy: title at top, panels below
- Cards use `rounded-md border border-slate-200 bg-white shadow-sm`

---

### shadcn/ui NOVA COMPONENT STYLE

All interactive and structural components follow **shadcn Nova** conventions:

**Cards / Panels**:
```
rounded-md border border-slate-200 bg-white shadow-sm
p-6
```

**Buttons (Primary)**:
```
inline-flex items-center justify-center rounded
bg-brand text-white
text-sm font-medium
h-10 px-4
hover:bg-brand/80
focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 focus-visible:ring-offset-2
transition-colors
```

**Buttons (Secondary / Ghost)**:
```
rounded border border-slate-200 bg-white text-slate-700
hover:bg-slate-100 hover:text-slate-900
text-sm font-medium h-10 px-4
```

**Inputs**:
```
flex h-10 w-full rounded border border-slate-200 bg-white
px-3 py-2 text-sm text-slate-900
placeholder:text-slate-400
focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 focus-visible:ring-offset-2
```

**Badges / Tags**:
```
inline-flex items-center rounded-sm
px-2.5 py-0.5 text-xs font-semibold
bg-slate-100 text-slate-700 border border-slate-200
```

**Badge (Brand accent)**:
```
bg-brand/10 text-brand border-brand/20
```

**Tabs**:
```
// Tab list
inline-flex h-10 items-center justify-center rounded bg-slate-100 p-1

// Tab trigger
rounded-sm px-3 py-1.5 text-sm font-medium text-slate-500
data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm
```

**Separator**:
```
h-px bg-slate-200
```

**Tooltip / Popover**:
```
rounded border border-slate-200 bg-white shadow-md
px-3 py-1.5 text-sm text-slate-700
```

**General Nova Principles**:
- `rounded-sm` (2px) on small elements (badges, tags, tab triggers)
- `rounded` (4px) on interactive elements (buttons, inputs, tooltips)
- `rounded-md` (6px) on cards and panels
- `rounded-lg` (8px) is the **maximum** — reserved for modals and hero containers only
- **Never use `rounded-xl`, `rounded-2xl`, or `rounded-full`** on structural elements
- Borders are always `border-slate-200`
- Shadows are `shadow-sm` (cards) or `shadow-md` (popovers, dropdowns)
- Focus rings use `ring-2 ring-brand/40 ring-offset-2`
- Transitions use `transition-colors` or `transition-all duration-200`
- No heavy drop shadows — subtle and editorial

---

## STEP 2: Illustration Style — Industrial Blueprint Editorial

### PROPORTIONS & FEEL
Grounded and realistic, NOT cartoonish. Slightly elongated Bauhaus-influenced figures. Detailed, expressive hands. Accurate equipment proportions. Should feel like **New Yorker** or **Harvard Business Review** editorial illustrations.

### CONCEPT: Visual Metaphors Only

**DO:**
- Show abstract concepts through physical metaphors (broken chains, tangled cables, cracked nodes)
- Use architectural and engineering visual language
- Show hands doing things
- Depict struggle, friction, or disconnection through the composition itself
- Use hatching, crosshatching, and technical linework textures

**DO NOT:**
- Use literal depictions of software, screens showing actual data, or real equipment
- Use generic business imagery (NO robots, light bulbs, targets, gears as decoration)
- Use warning symbols, error icons, or exclamation marks **inside illustrations** (these are allowed in functional UI for true error states only)
- Add text labels, captions, or annotations inside illustrations
- Use clip art or abstract icons
- Use any accent color other than Factory Blue (`#0052CC`)

### PALETTE FOR ILLUSTRATIONS

- **Linework**: #000000 (black) and #374151 (industrial gray)
- **Shadows/depth**: #1a1d29 at 15-30% opacity
- **Paper tone**: #f5f3ef (cream)
- **Single accent**: #0052CC (Factory Blue) on ONE element per panel that represents the core problem or concept

---


## STEP 3: Tailwind Config Snippet

```js
// tailwind.config.js — 8090 Design System
const config = {
  theme: {
    extend: {
      colors: {
        brand: '#0052CC',  // Use Tailwind opacity modifier: bg-brand/10, text-brand/40, etc.
        // All neutrals use Tailwind's built-in slate — no overrides needed
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'Cascadia Code', 'monospace'],
      },
      borderRadius: {
        sm: '2px',    // badges, tags, small elements
        DEFAULT: '4px', // buttons, inputs, most elements
        md: '6px',    // cards, panels
        lg: '8px',    // modals, hero sections (maximum)
      },
    },
  },
}
export default config
```

---

## STEP 4: Prototype Preflight Checklist

Before finalizing any prototype, verify every item:

- [ ] **Slate palette only** — no stray grays from zinc, neutral, or stone
- [ ] **Factory Blue (`#0052CC`)** is the ONLY accent color — no other hues
- [ ] **One blue accent** per panel, highlighting the core concept
- [ ] **No text inside illustrations** — headlines live outside illustration panels
- [ ] **No warning symbols**, error icons, or exclamation marks **in illustrations** (allowed in functional UI for true errors)
- [ ] **Illustrations are metaphorical**, not literal depictions of software/screens
- [ ] **Blueprint/technical linework** with hatching texture in slate tones
- [ ] **Background is `slate-50`** (`#f8fafc`), not pure white or warm cream
- [ ] **Cards use Nova style**: `rounded-md border-slate-200 bg-white shadow-sm`
- [ ] **Corner radii are low**: max `rounded-lg` (8px), most elements `rounded` (4px) or `rounded-sm` (2px) — no `rounded-xl` or higher
- [ ] **Spacing follows 8px grid** — only Tailwind spacing tokens (2, 4, 6, 8, 12, 16)
- [ ] **Focus states** use `ring-brand/40` — not default blue or purple
- [ ] **Buttons follow Nova spec** — `rounded` (4px), proper height (`h-10`), font-medium
- [ ] **Brand variants use opacity only** — `bg-brand/10`, `text-brand/60`, etc. — no separate hex tints
- [ ] **No gradients** on UI surfaces
- [ ] **Typography uses IBM Plex Sans** — no Inter, Roboto, Geist Sans, or system defaults
- [ ] **Monospace uses Geist Mono** for data labels and code
- [ ] **Responsive**: works at `sm`, `md`, and `lg` breakpoints minimum

---

## QUICK REFERENCE: Class Cheatsheet

```
// Page background
bg-slate-50

// Card
rounded-md border border-slate-200 bg-white shadow-sm p-6

// Headline
text-4xl font-bold text-slate-950 tracking-tight

// Section header
text-2xl font-semibold text-slate-950 tracking-tight

// Body text
text-base text-slate-700

// Caption
text-sm text-slate-500 font-medium

// Overline label
text-xs font-semibold uppercase tracking-widest text-slate-400

// Primary button
rounded bg-brand text-white text-sm font-medium h-10 px-4 hover:bg-brand/80

// Secondary button
rounded border border-slate-200 bg-white text-slate-700 text-sm font-medium h-10 px-4 hover:bg-slate-100

// Input
rounded border border-slate-200 bg-white h-10 px-3 text-sm text-slate-900 placeholder:text-slate-400

// Divider
h-px bg-slate-200

// Brand badge
rounded-sm bg-brand/10 text-brand text-xs font-semibold px-2.5 py-0.5 border border-brand/20
```
