---
name: SafeRide NG
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0edec'
  surface-container-high: '#ebe7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1c1b1b'
  on-surface-variant: '#43474f'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#1b6d24'
  on-secondary: '#ffffff'
  secondary-container: '#a0f399'
  on-secondary-container: '#217128'
  tertiary: '#460003'
  on-tertiary: '#ffffff'
  tertiary-container: '#6e0008'
  on-tertiary-container: '#ff6d63'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  primary-fixed-variant: '#1f477b'
  secondary-fixed: '#a3f69c'
  secondary-fixed-dim: '#88d982'
  on-secondary-fixed: '#002204'
  on-secondary-fixed-variant: '#005312'
  tertiary-fixed: '#ffdad6'
  tertiary-fixed-dim: '#ffb4ac'
  on-tertiary-fixed: '#410003'
  on-tertiary-fixed-variant: '#93000e'
  background: '#fcf9f8'
  on-background: '#1c1b1b'
  surface-variant: '#e5e2e1'

typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 60px
    letterSpacing: -0.02em
  display-sm:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style
The design system for SafeRide NG is rooted in the concepts of **Civic Trust, Architectural Security, and Urban Connectivity**. It serves as a digital infrastructure for Nigerian commuters and authorities, balancing a high-tech "Smart City" aesthetic with the warmth of accessible public service.

The visual direction is **Modern Corporate with a Glassmorphic edge**. It avoids the clutter of traditional government portals, opting instead for expansive whitespace, precision-engineered components, and subtle depth. The goal is to evoke a sense of "watchful calm"—professional, reliable, and technologically advanced. Visual motifs should subtly reference Nigerian urban grids through structured layouts and interconnected line patterns in background decorations.

## Colors
The palette is dominated by **Heritage Blue**, establishing immediate institutional trust. **Security Green** is reserved strictly for "Verified" and "Safe" states, while **Alert Red** is used sparingly for SOS functions to maintain high psychological impact.

In **Dark Mode**, surfaces should use the neutral-900 base with a 2% blue tint to avoid pure black, maintaining the premium "tech" feel. Glassmorphic elements should utilize white transulcence at 10% in light mode and 5% in dark mode to create a sophisticated layered effect without sacrificing legibility.

## Typography
We utilize **Inter** across all levels for its exceptional legibility and systematic feel. The hierarchy is "top-heavy," using bold display sizes for critical security statuses and navigation headers.

- **Display levels** use tight letter-spacing to emphasize the modern, architectural feel.
- **Label styles** use slightly increased weight (600) to ensure high-contrast readability against both solid and glassmorphic backgrounds.
- **Mobile scaling**: On screens smaller than 768px, Display and Headline sizes should scale down by one level to ensure content density remains appropriate for on-the-go usage.

## Layout & Spacing
The system employs an **8px base grid** to ensure mathematical harmony across all components.

- **Desktop Layout**: A 12-column fluid grid with 24px gutters and 48px side margins. Central content containers should cap at 1280px to maintain readability.
- **Mobile Layout**: A 4-column grid with 16px gutters and 16px margins.
- **Rhythm**: Vertical rhythm is driven by the 16px (md) and 24px (lg) increments. Component-internal spacing should generally stay at 12px or 16px to maintain a dense, professional "dashboard" feel without feeling cramped.

## Elevation & Depth
Depth in the design system is achieved through a combination of **Ambient Shadows** and **Glassmorphism**.

- **Level 1 (Base)**: Flat background with subtle blue tint.
- **Level 2 (Cards)**: Soft, diffused shadow (0px 4px 20px rgba(0, 51, 102, 0.08)).
- **Level 3 (Overlays/Headers)**: Glassmorphism with a `backdrop-filter: blur(12px)` and a thin 1px border (white at 20% opacity). This level is used for top navigation and sticky floating action bars.
- **Interaction**: On hover, cards should lift slightly using a more pronounced shadow to provide tactile feedback.

## Shapes
A **Rounded** shape language is utilized to soften the professional tone, making the tech feel more "human" and approachable.

- **Standard Elements**: Buttons and input fields use a 0.5rem (8px) radius.
- **Containers**: Information cards and security modules use a 1rem (16px) radius to create a distinct framing effect.
- **Status Pills**: Elements like "Verified" or "Active" badges should use the `rounded-full` (pill) property to differentiate them from functional buttons.

## Components

### SOS Button
The most critical component. It uses **Alert Red (#C62828)** with a slight outer glow (pulse animation in active states). It is always circular or pill-shaped to stand out from rectangular UI elements.

### Security Cards
Cards representing drivers or vehicles. They feature a high-contrast top-right area for **Verification Badges**. Use a subtle light-gray border (1px) to define edges against the background tint.

### Glassmorphic Headers
The main navigation bar uses a backdrop-blur (12px) with a bottom border of 1px (Neutral-300 at 50% opacity). This keeps the "Nigerian Urban Grid" background visible while ensuring text clarity.

### Status Indicators
- **Verified**: Security Green with a check icon.
- **Pending**: Neutral-600 with an info icon.
- **Flagged**: Alert Red with a warning icon.

### Input Fields
Fields use a solid white background in light mode with a 1px Neutral-300 border. On focus, the border transitions to Primary Deep Blue with a 2px outer "halo" of the same color at 10% opacity.

### Verification Badges
Small, pill-shaped components using a light green surface and dark green text. These should be placed consistently in the top-right of profile-related cards to immediately build trust.

