# WCAG 2.1 AA Accessibility Checklist

This checklist guides frontend developers through the WCAG 2.1 Level AA
requirements for PROBEXR. Apply these when building or reviewing UI components.

## 1. Perceivable

### 1.1 Text Alternatives
- [ ] All `<img>` tags have descriptive `alt` attributes
- [ ] Decorative images use `alt=""`
- [ ] Icon-only buttons have `aria-label` or visually hidden text
- [ ] Charts/graphs have text alternatives or data tables

### 1.2 Color & Contrast
- [ ] Text contrast ratio ≥ 4.5:1 (normal text)
- [ ] Large text (18px+ bold or 24px+) contrast ratio ≥ 3:1
- [ ] UI component and graphical object contrast ≥ 3:1
- [ ] Information is never conveyed by color alone
- [ ] Use a tool: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### 1.3 Content Structure
- [ ] Single `<h1>` per page, proper heading hierarchy (h1 → h2 → h3)
- [ ] Lists use `<ul>`, `<ol>`, `<dl>` — not styled divs
- [ ] Tables use `<th>`, `scope`, and `<caption>`
- [ ] Forms use `<label>` linked to inputs via `for`/`id`

### 1.4 Responsive & Reflow
- [ ] Content reflows at 320px width without horizontal scrolling
- [ ] Text can be resized to 200% without loss of content
- [ ] Touch targets are at least 44×44px

## 2. Operable

### 2.1 Keyboard
- [ ] All interactive elements are focusable and operable via keyboard
- [ ] No keyboard traps (user can Tab in and out of every component)
- [ ] Visible focus indicators on all focusable elements
- [ ] Skip-to-content link as first focusable element
- [ ] Modal dialogs trap focus correctly and restore on close

### 2.2 Navigation
- [ ] Page titles are unique and descriptive
- [ ] Focus order matches visual layout (left-to-right, top-to-bottom)
- [ ] Multi-step processes indicate current step

### 2.3 Timing
- [ ] No content auto-updates without user control
- [ ] Session timeouts give 20+ second warning with extend option
- [ ] No content flashes more than 3 times per second

## 3. Understandable

### 3.1 Language
- [ ] `<html lang="en">` is set
- [ ] Foreign language passages use `lang` attribute

### 3.2 Forms
- [ ] Required fields are clearly marked (not just with color)
- [ ] Error messages are descriptive and adjacent to the field
- [ ] Error messages use `aria-describedby` or `aria-errormessage`
- [ ] Success/error states are announced to screen readers (`aria-live`)

### 3.3 Predictable
- [ ] Inputs don't trigger unexpected actions on focus or change
- [ ] Navigation is consistent across pages
- [ ] Labels and icons are used consistently

## 4. Robust

### 4.1 ARIA
- [ ] Use native HTML elements before ARIA (`<button>` not `<div role="button">`)
- [ ] Custom widgets follow WAI-ARIA Authoring Practices
- [ ] `aria-expanded`, `aria-selected`, `aria-checked` used correctly
- [ ] Dynamic content updates use `aria-live="polite"` or `"assertive"`

### 4.2 Validation
- [ ] HTML validates (no duplicate IDs)
- [ ] All interactive elements have accessible names
- [ ] Test with: axe DevTools, Lighthouse, NVDA/VoiceOver

## Automated Testing Tools

| Tool | Type | Usage |
|------|------|-------|
| [axe-core](https://github.com/dequelabs/axe-core) | Automated | `npm install @axe-core/react` |
| [Lighthouse](https://developer.chrome.com/docs/lighthouse/) | Audit | Chrome DevTools > Lighthouse > Accessibility |
| [WAVE](https://wave.webaim.org/) | Browser ext | Visual accessibility report |
| [pa11y](https://pa11y.org/) | CLI | `npx pa11y http://localhost:5173` |
| VoiceOver | Manual | macOS: Cmd+F5 to toggle |

## Priority Implementation Order

1. **Critical** (blocks users): Keyboard nav, focus management, alt text, form labels
2. **High** (degrades UX): Color contrast, heading structure, error messages
3. **Medium** (best practice): ARIA landmarks, skip links, responsive reflow
4. **Low** (polish): Language attributes, consistent naming, timing controls
