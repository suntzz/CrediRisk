import React from 'react';

export interface MagicBentoCardData {
  id?: string | number;
  color?: string;
  title?: string;
  description?: string;
  label?: string;
  className?: string;
  style?: React.CSSProperties;
  glowColor?: string;
  particleCount?: number;
  enableTilt?: boolean;
  clickEffect?: boolean;
  enableMagnetism?: boolean;
  onClick?: (e: React.MouseEvent<HTMLElement>) => void;
  ariaLabel?: string;
  content?: React.ReactNode | ((card: MagicBentoCardData) => React.ReactNode);
}

export interface ParticleCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
  className?: string;
  disableAnimations?: boolean;
  style?: React.CSSProperties;
  particleCount?: number;
  glowColor?: string;
  enableTilt?: boolean;
  clickEffect?: boolean;
  enableMagnetism?: boolean;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLDivElement>) => void;
  role?: string;
  tabIndex?: number;
  'aria-label'?: string;
}

export interface BentoCardGridProps {
  children?: React.ReactNode;
  gridRef?: React.RefObject<HTMLDivElement | null>;
  className?: string;
  style?: React.CSSProperties;
}

export interface GlobalSpotlightProps {
  gridRef?: React.RefObject<HTMLDivElement | null>;
  disableAnimations?: boolean;
  enabled?: boolean;
  spotlightRadius?: number;
  glowColor?: string;
  blendMode?: string;
}

export interface MagicBentoProps {
  cards?: MagicBentoCardData[];
  children?: React.ReactNode;
  className?: string;
  gridClassName?: string;
  style?: React.CSSProperties;
  gridStyle?: React.CSSProperties;
  textAutoHide?: boolean;
  enableStars?: boolean;
  enableSpotlight?: boolean;
  enableBorderGlow?: boolean;
  disableAnimations?: boolean;
  spotlightRadius?: number;
  particleCount?: number;
  enableTilt?: boolean;
  glowColor?: string;
  clickEffect?: boolean;
  enableMagnetism?: boolean;
  blendMode?: string;
}

export declare const ParticleCard: React.FC<ParticleCardProps>;
export declare const BentoCardGrid: React.FC<BentoCardGridProps>;
export declare const GlobalSpotlight: React.FC<GlobalSpotlightProps>;
declare const MagicBento: React.FC<MagicBentoProps>;

export default MagicBento;
export { MagicBento };
