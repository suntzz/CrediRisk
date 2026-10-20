export interface BadgeStudent {
  id: number;
  nombre: string;
  codigo: string;
  correo: string;
  iniciales: string;
  badgeUrl?: string;
  foto?: string;
}

export const TEAM_MEMBERS: BadgeStudent[] = [
  {
    id: 1,
    nombre: 'Leidy Vanessa Guecha Alape',
    codigo: '67001077',
    correo: 'lvguecha77@ucatolica.edu.co',
    iniciales: 'LG',
    badgeUrl: '/team/badge-1.png?v=5',
    foto: '/team/leidy.png?v=5',
  },
  {
    id: 2,
    nombre: 'Sharick Natalia Hernández Gómez',
    codigo: '67000979',
    correo: 'snhernandez79@ucatolica.edu.co',
    iniciales: 'SH',
    badgeUrl: '/team/badge-2.png?v=5',
    foto: '/team/sharick.png?v=5',
  },
  {
    id: 3,
    nombre: 'Laura Sofia Diaz Suarez',
    codigo: '67000991',
    correo: 'lsdiaz91@ucatolica.edu.co',
    iniciales: 'LD',
    badgeUrl: '/team/badge-3.png?v=5',
    foto: '/team/laura.png?v=5',
  },
  {
    id: 4,
    nombre: 'Iván Camilo Solano Sánchez',
    codigo: '67001118',
    correo: 'icsolano18@ucatolica.edu.co',
    iniciales: 'IS',
    badgeUrl: '/team/badge-4.png?v=5',
    foto: '/team/ivan.png?v=5',
  },
  {
    id: 5,
    nombre: 'Cristian Camilo Martínez Delgado',
    codigo: '67001140',
    correo: 'ccmartinez40@ucatolica.edu.co',
    iniciales: 'CM',
    badgeUrl: '/team/badge-5.png?v=5',
    foto: '/team/cristian.png?v=5',
  },
];

export function generateBadgeDataUrls(student: BadgeStudent): { front: string; back: string } {
  if (student.badgeUrl) {
    return {
      front: student.badgeUrl,
      back: '/brand/credirisk-card-back.png?v=5',
    };
  }

  return {
    front: `/team/badge-${student.id}.png?v=5`,
    back: '/brand/credirisk-card-back.png?v=5',
  };
}
