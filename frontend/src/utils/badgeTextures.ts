export interface BadgeStudent {
  id: number;
  nombre: string;
  codigo: string;
  correo: string;
  iniciales: string;
}

export const TEAM_MEMBERS: BadgeStudent[] = [
  {
    id: 1,
    nombre: 'Leidy Vanessa Guecha Alape',
    codigo: '67001077',
    correo: 'lvguecha77@ucatolica.edu.co',
    iniciales: 'LG',
  },
  {
    id: 2,
    nombre: 'Sharick Natalia Hernández Gómez',
    codigo: '67000979',
    correo: 'snhernandez79@ucatolica.edu.co',
    iniciales: 'SH',
  },
  {
    id: 3,
    nombre: 'Laura Sofia Diaz Suarez',
    codigo: '67000991',
    correo: 'lsdiaz91@ucatolica.edu.co',
    iniciales: 'LD',
  },
  {
    id: 4,
    nombre: 'Iván Camilo Solano Sánchez',
    codigo: '67001118',
    correo: 'icsolano18@ucatolica.edu.co',
    iniciales: 'IS',
  },
  {
    id: 5,
    nombre: 'Cristian Camilo Martínez Delgado',
    codigo: '67001140',
    correo: 'ccmartinez40@ucatolica.edu.co',
    iniciales: 'CM',
  },
];

export function generateBadgeDataUrls(student: BadgeStudent): { front: string; back: string } {
  if (typeof document === 'undefined') {
    return { front: '', back: '' };
  }

  const width = 800;
  const height = 1125; // 1.6 : 2.25 aspect ratio matching Lanyard portrait

  // 1. FRONT FACE
  const frontCanvas = document.createElement('canvas');
  frontCanvas.width = width;
  frontCanvas.height = height;
  const fCtx = frontCanvas.getContext('2d');

  if (fCtx) {
    // Background
    const bgGrad = fCtx.createLinearGradient(0, 0, width, height);
    bgGrad.addColorStop(0, '#0b1120');
    bgGrad.addColorStop(0.5, '#0f172a');
    bgGrad.addColorStop(1, '#020617');
    fCtx.fillStyle = bgGrad;
    fCtx.fillRect(0, 0, width, height);

    // Top Header Banner
    const bannerGrad = fCtx.createLinearGradient(0, 0, width, 0);
    bannerGrad.addColorStop(0, '#1d4ed8');
    bannerGrad.addColorStop(0.5, '#2563eb');
    bannerGrad.addColorStop(1, '#3b82f6');
    fCtx.fillStyle = bannerGrad;
    fCtx.fillRect(0, 0, width, 140);

    // University Header Text
    fCtx.textAlign = 'center';
    fCtx.fillStyle = '#ffffff';
    fCtx.font = 'bold 26px "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
    fCtx.fillText('UNIVERSIDAD CATÓLICA DE COLOMBIA', width / 2, 60);

    fCtx.font = '600 17px "JetBrains Mono", monospace';
    fCtx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    fCtx.fillText('FACULTAD DE INGENIERÍA · SISTEMAS', width / 2, 92);

    fCtx.font = '500 13px "JetBrains Mono", monospace';
    fCtx.fillStyle = 'rgba(255, 255, 255, 0.75)';
    fCtx.fillText('CREDIRISK NEURAL LAB', width / 2, 118);

    // Decorative Gold Accent Line
    fCtx.fillStyle = '#f59e0b';
    fCtx.fillRect(0, 140, width, 4);

    // Lanyard Slot Indicator (visual cut out border)
    fCtx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    fCtx.lineWidth = 2;
    fCtx.strokeRect(width / 2 - 80, 155, 160, 24);

    // Center Avatar Container (Monogram)
    const avatarY = 350;
    const avatarRadius = 110;

    // Outer glow circle
    const glowGrad = fCtx.createRadialGradient(width / 2, avatarY, 80, width / 2, avatarY, 150);
    glowGrad.addColorStop(0, 'rgba(37, 99, 235, 0.4)');
    glowGrad.addColorStop(1, 'rgba(37, 99, 235, 0)');
    fCtx.fillStyle = glowGrad;
    fCtx.beginPath();
    fCtx.arc(width / 2, avatarY, 150, 0, Math.PI * 2);
    fCtx.fill();

    // Monogram Circle Background
    fCtx.fillStyle = '#1e293b';
    fCtx.beginPath();
    fCtx.arc(width / 2, avatarY, avatarRadius, 0, Math.PI * 2);
    fCtx.fill();

    // Circle Border
    fCtx.strokeStyle = '#3b82f6';
    fCtx.lineWidth = 6;
    fCtx.beginPath();
    fCtx.arc(width / 2, avatarY, avatarRadius, 0, Math.PI * 2);
    fCtx.stroke();

    // Initials Text
    fCtx.textAlign = 'center';
    fCtx.textBaseline = 'middle';
    fCtx.fillStyle = '#60a5fa';
    fCtx.font = 'bold 84px "JetBrains Mono", monospace';
    fCtx.fillText(student.iniciales, width / 2, avatarY);

    // Student Name
    fCtx.textBaseline = 'alphabetic';
    fCtx.fillStyle = '#ffffff';
    fCtx.font = 'bold 34px "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
    fCtx.fillText(student.nombre.toUpperCase(), width / 2, 540);

    // Role / Credential Type Pill
    const pillY = 575;
    const pillWidth = 320;
    const pillHeight = 36;
    fCtx.fillStyle = 'rgba(30, 58, 138, 0.7)';
    fCtx.beginPath();
    fCtx.roundRect(width / 2 - pillWidth / 2, pillY, pillWidth, pillHeight, 18);
    fCtx.fill();
    fCtx.strokeStyle = 'rgba(96, 165, 250, 0.6)';
    fCtx.lineWidth = 1.5;
    fCtx.stroke();

    fCtx.fillStyle = '#93c5fd';
    fCtx.font = '600 15px "JetBrains Mono", monospace';
    fCtx.fillText('CREDENCIAL DE INVESTIGADOR', width / 2, pillY + 24);

    // Code and Email Box
    const boxY = 660;
    const boxWidth = 660;
    const boxHeight = 190;
    fCtx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    fCtx.beginPath();
    fCtx.roundRect(width / 2 - boxWidth / 2, boxY, boxWidth, boxHeight, 16);
    fCtx.fill();
    fCtx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
    fCtx.lineWidth = 2;
    fCtx.stroke();

    // Inner Code
    fCtx.textAlign = 'left';
    fCtx.fillStyle = '#94a3b8';
    fCtx.font = '600 16px "JetBrains Mono", monospace';
    fCtx.fillText('CÓDIGO INSTITUCIONAL', width / 2 - boxWidth / 2 + 36, boxY + 46);

    fCtx.fillStyle = '#38bdf8';
    fCtx.font = 'bold 28px "JetBrains Mono", monospace';
    fCtx.fillText(student.codigo, width / 2 - boxWidth / 2 + 36, boxY + 82);

    // Separator Line
    fCtx.strokeStyle = 'rgba(51, 65, 85, 0.6)';
    fCtx.beginPath();
    fCtx.moveTo(width / 2 - boxWidth / 2 + 36, boxY + 104);
    fCtx.lineTo(width / 2 + boxWidth / 2 - 36, boxY + 104);
    fCtx.stroke();

    // Inner Email
    fCtx.fillStyle = '#94a3b8';
    fCtx.font = '600 16px "JetBrains Mono", monospace';
    fCtx.fillText('CORREO INSTITUCIONAL', width / 2 - boxWidth / 2 + 36, boxY + 138);

    fCtx.fillStyle = '#e2e8f0';
    fCtx.font = 'bold 22px "JetBrains Mono", monospace';
    fCtx.fillText(student.correo, width / 2 - boxWidth / 2 + 36, boxY + 168);

    // Simulated Barcode at bottom
    const barcodeY = 910;
    fCtx.fillStyle = '#ffffff';
    fCtx.fillRect(width / 2 - 250, barcodeY, 500, 65);

    // Draw realistic barcode stripes
    fCtx.fillStyle = '#000000';
    let currentX = width / 2 - 230;
    const seed = (student.id * 17 + parseInt(student.codigo.slice(-4), 10)) % 1000;
    for (let i = 0; i < 68; i++) {
      const barWidth = ((i * 7 + seed) % 5 === 0) ? 5 : ((i % 3 === 0) ? 3 : 1.5);
      if ((i * 11 + seed) % 7 !== 2) {
        fCtx.fillRect(currentX, barcodeY + 6, barWidth, 53);
      }
      currentX += barWidth + 3;
      if (currentX > width / 2 + 230) break;
    }

    // Bottom Footer
    fCtx.textAlign = 'center';
    fCtx.fillStyle = '#64748b';
    fCtx.font = '500 14px "JetBrains Mono", monospace';
    fCtx.fillText(`VERIFICACIÓN DE AUTENTICIDAD · ID: ${student.codigo}`, width / 2, 1030);

    fCtx.font = '500 12px "Inter", sans-serif';
    fCtx.fillStyle = '#475569';
    fCtx.fillText('Bogotá D.C., Colombia · Redes Neuronales Profundas', width / 2, 1060);
  }

  return {
    front: frontCanvas.toDataURL('image/png'),
    back: '/brand/credirisk-card-back.png'
  };
}

