import React from 'react';

export interface PillNavItem {
  label: string;
  href?: string;
  ariaLabel?: string;
  onClick?: (e?: React.MouseEvent) => void;
}

export interface PillNavProps {
  logo?: string;
  logoAlt?: string;
  items: PillNavItem[];
  activeHref?: string;
  className?: string;
  ease?: string;
  baseColor?: string;
  pillColor?: string;
  hoveredPillTextColor?: string;
  pillTextColor?: string;
  onMobileMenuClick?: () => void;
  initialLoadAnimation?: boolean;
}

declare const PillNav: React.FC<PillNavProps>;
export default PillNav;
export { PillNav };
