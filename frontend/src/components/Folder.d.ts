import React from 'react';

export interface FolderItem {
  title?: string;
  description?: string;
  image?: string;
  alt?: string;
  content?: React.ReactNode;
}

export interface FolderProps {
  items?: (FolderItem | string | number | React.ReactNode)[];
  label?: string;
  mode?: 'flap' | 'book';
  variant?: 'solid' | 'glass' | 'matte';
  color?: string;
  paperColor?: string;
  tabPosition?: 'left' | 'center' | 'right';
  layout?: 'spread' | 'stack' | 'row';
  size?: number;
  openOn?: 'click' | 'hover';
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  onItemClick?: (item: any, index: number) => void;
  onItemDrop?: (item: any, index: number) => void;
  draggable?: boolean;
  zoomOnClick?: boolean;
  peek?: boolean;
  intro?: boolean;
  tilt?: number;
  bounce?: number;
  speed?: number;
  frost?: number;
  closeOnOutsideClick?: boolean;
  theme?: 'dark' | 'light';
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

declare const Folder: React.FC<FolderProps>;
export default Folder;
export { Folder };
