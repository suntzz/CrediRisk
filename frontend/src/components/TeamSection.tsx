import React, { useEffect, useRef, useState } from 'react';
import { 
  Users, 
  Mail, 
  IdCard, 
  Sparkles,
  Copy,
  Check
} from 'lucide-react';
import { Folder } from './Folder';
import { useTheme } from '../context/ThemeContext';
import { gsap } from 'gsap';

export interface TeamMember {
  id: string;
  nombre: string;
  codigo: string;
  correo: string;
}

const TEAM_MEMBERS: TeamMember[] = [
  {
    id: 'vanessa-guecha',
    nombre: 'Leidy Vanessa Guecha Alape',
    codigo: '67001077',
    correo: 'lvguecha77@ucatolica.edu.co'
  },
  {
    id: 'sharick-hernandez',
    nombre: 'Sharick Natalia Hernández Gómez',
    codigo: '67000979',
    correo: 'snhernandez79@ucatolica.edu.co'
  },
  {
    id: 'laura-diaz',
    nombre: 'Laura Sofia Diaz Suarez',
    codigo: '67000991',
    correo: 'lsdiaz91@ucatolica.edu.co'
  },
  {
    id: 'ivan-solano',
    nombre: 'Iván Camilo Solano Sánchez',
    codigo: '67001118',
    correo: 'icsolano18@ucatolica.edu.co'
  },
  {
    id: 'cristian-martinez',
    nombre: 'Cristian Camilo Martínez Delgado',
    codigo: '67001140',
    correo: 'ccmartinez40@ucatolica.edu.co'
  }
];

export const TeamSection: React.FC = () => {
  const { isDark } = useTheme();
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const showcaseRef = useRef<HTMLDivElement>(null);
  const cardsContainerRef = useRef<HTMLDivElement>(null);
  const [isFolderOpen, setIsFolderOpen] = useState<boolean>(false);
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [hasAnimated, setHasAnimated] = useState<boolean>(false);

  // Progressive scroll entrance observer using GSAP
  useEffect(() => {
    const section = sectionRef.current;
    if (!section || hasAnimated) return;

    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const observer = new IntersectionObserver(
      entries => {
        const [entry] = entries;
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);

          if (prefersReduced) {
            if (headerRef.current) headerRef.current.style.opacity = '1';
            if (showcaseRef.current) showcaseRef.current.style.opacity = '1';
            if (cardsContainerRef.current) {
              const cards = cardsContainerRef.current.children;
              Array.from(cards).forEach(card => {
                (card as HTMLElement).style.opacity = '1';
              });
            }
            return;
          }

          // 1. Reveal Section Header
          if (headerRef.current) {
            gsap.fromTo(
              headerRef.current,
              { opacity: 0, y: 24 },
              { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
            );
          }

          // 2. Reveal Central Folder Showcase
          if (showcaseRef.current) {
            gsap.fromTo(
              showcaseRef.current,
              { opacity: 0, y: 32, scale: 0.96 },
              { opacity: 1, y: 0, scale: 1, duration: 0.7, delay: 0.15, ease: 'power3.out' }
            );
          }

          // 3. Staggered Entrance of Member Cards
          if (cardsContainerRef.current) {
            const cards = cardsContainerRef.current.querySelectorAll('.team-card-item');
            gsap.fromTo(
              cards,
              { opacity: 0, y: 28 },
              {
                opacity: 1,
                y: 0,
                duration: 0.65,
                stagger: 0.08,
                delay: 0.25,
                ease: 'power3.out'
              }
            );
          }

          observer.disconnect();
        }
      },
      {
        root: null,
        threshold: 0.12,
        rootMargin: '0px 0px -40px 0px'
      }
    );

    observer.observe(section);

    return () => observer.disconnect();
  }, [hasAnimated]);

  const handleCopyEmail = (email: string) => {
    navigator.clipboard.writeText(email);
    setCopiedEmail(email);
    setTimeout(() => {
      setCopiedEmail(null);
    }, 2000);
  };

  // 5 documentos correspondientes a cada integrante dentro de la única carpeta
  const folderItems = TEAM_MEMBERS.map(member => ({
    title: member.nombre,
    description: `Código: ${member.codigo}\n${member.correo}`
  }));

  return (
    <section
      id="sobre-nosotros"
      ref={sectionRef}
      className="relative z-10 w-full max-w-6xl mx-auto px-6 pt-16 pb-20 scroll-mt-20 border-t border-slate-200/70 dark:border-slate-800/60"
      aria-label="Sección Sobre nosotros: Equipo del proyecto"
    >
      {/* Encabezado limpio de la sección */}
      <div ref={headerRef} className="max-w-3xl mb-8 opacity-0">
        <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md text-[11px] font-mono uppercase tracking-[0.14em] font-semibold bg-blue-50 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300 border border-blue-200/80 dark:border-blue-900/60 mb-3.5">
          <Users className="w-3.5 h-3.5" />
          <span>Equipo del Proyecto</span>
        </div>

        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-display font-extrabold text-slate-950 dark:text-white tracking-tight mb-2">
          Sobre nosotros
        </h2>

        <div className="flex items-center space-x-2 text-xs font-mono text-slate-500 dark:text-slate-400">
          <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-cyan-400" />
          <span>Haz clic en la carpeta para desplegar los documentos de los integrantes</span>
        </div>
      </div>

      {/* Contenedor central de la única carpeta con los 5 integrantes */}
      <div
        ref={showcaseRef}
        className="w-full mb-12 opacity-0 bg-slate-50/70 dark:bg-slate-900/50 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 p-8 sm:p-12 flex flex-col items-center justify-center relative overflow-visible shadow-xs"
      >
        <div className="transform transition-transform duration-200 hover:scale-[1.02]">
          <Folder
            items={folderItems}
            label="Sobre nosotros"
            mode="flap"
            variant="solid"
            layout="spread"
            color="#3d8bff"
            paperColor="#ffffff"
            tabPosition="right"
            openOn="click"
            size={1.3}
            frost={0.25}
            tilt={0.5}
            speed={1}
            bounce={0.5}
            peek={true}
            intro={true}
            draggable={true}
            zoomOnClick={true}
            theme={isDark ? 'dark' : 'light'}
            open={isFolderOpen}
            onOpenChange={setIsFolderOpen}
            className="select-none"
          />
        </div>
      </div>

      {/* Listado estructurado y accesible de los 5 integrantes */}
      <div
        ref={cardsContainerRef}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-5 items-stretch"
      >
        {TEAM_MEMBERS.map((member, index) => {
          let colSpanClass = 'lg:col-span-2';
          if (index === 3) {
            colSpanClass = 'lg:col-start-2 lg:col-span-2';
          } else if (index === 4) {
            colSpanClass = 'lg:col-span-2';
          }

          return (
            <div
              key={member.id}
              className={`team-card-item ${colSpanClass} opacity-0 bg-white dark:bg-slate-900/90 rounded-xl p-5 border border-slate-200/90 dark:border-slate-800 transition-all duration-200 hover:border-blue-400/60 dark:hover:border-blue-500/50 hover:shadow-xs flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2.5">
                  <h3 className="font-display font-bold text-base text-slate-950 dark:text-white leading-snug">
                    {member.nombre}
                  </h3>
                  <div
                    className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 border border-blue-200/60 dark:border-blue-900/40"
                    title="Documento de identidad"
                  >
                    <IdCard className="w-3.5 h-3.5" />
                  </div>
                </div>

                <div className="flex items-center space-x-2 text-xs mb-3">
                  <span className="text-slate-500 dark:text-slate-400 font-sans">
                    Código:
                  </span>
                  <span className="font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200/80 dark:border-slate-700/80">
                    {member.codigo}
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2">
                <div className="flex items-center space-x-2 text-xs min-w-0">
                  <Mail className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500 shrink-0" />
                  <a
                    href={`mailto:${member.correo}`}
                    className="font-mono text-xs text-blue-600 dark:text-sky-400 hover:underline truncate"
                    title={`Escribir a ${member.correo}`}
                  >
                    {member.correo}
                  </a>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopyEmail(member.correo)}
                  className="shrink-0 p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                  title="Copiar correo institucional"
                  aria-label={`Copiar correo de ${member.nombre}`}
                >
                  {copiedEmail === member.correo ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default TeamSection;
