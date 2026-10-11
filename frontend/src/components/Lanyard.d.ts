import React from 'react';

export interface LanyardProps {
  frontImage?: string;
  backImage?: string;
  imageFit?: 'cover' | 'contain' | 'Cover' | 'Contain';
  cardColor?: string;
  orientation?: 'portrait' | 'landscape' | 'Portrait' | 'Landscape';
  finish?: 'glossy' | 'matte' | 'holographic' | 'metallic' | 'Glossy' | 'Matte' | 'Holographic' | 'Metallic';
  cornerRadius?: number;
  size?: number;
  anchor?: 'left' | 'center' | 'right' | 'Left' | 'Center' | 'Right';
  strapLength?: number;
  strapImage?: string;
  strapColor?: string;
  strapWidth?: number;
  bandLength?: number;
  bandWidth?: number;
  bandColor?: string;
  bandImage?: string;
  plainBand?: boolean;
  metal?: 'silver' | 'gold' | 'graphite' | 'Silver' | 'Gold' | 'Graphite';
  gravity?: number;
  damping?: number;
  elasticity?: number;
  breeze?: number;
  interactive?: boolean;
  intro?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export declare const Lanyard: React.FC<LanyardProps>;
export default Lanyard;
