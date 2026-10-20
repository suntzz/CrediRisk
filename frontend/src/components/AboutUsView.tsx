import React, { useMemo, useState } from 'react';
import { 
  Copy, 
  Check, 
  FileCheck2,
  FlaskConical
} from 'lucide-react';
import { Lanyard } from './Lanyard';
import { generateBadgeDataUrls, TEAM_MEMBERS } from '../utils/badgeTextures';

interface AboutUsViewProps {
  onBackToHome: () => void;
  onOpenEvaluator: () => void;
  onOpenLab: () => void;
}

export const AboutUsView: React.FC<AboutUsViewProps> = ({
  onBackToHome,
  onOpenEvaluator,
  onOpenLab,
}) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Generate crisp 3D badge card textures once
  const textures = useMemo(() => {
    const map: Record<number, { front: string; back: string }> = {};
    TEAM_MEMBERS.forEach((m) => {
      map[m.id] = generateBadgeDataUrls(m);
    });
    return map;
  }, []);

  const copyToClipboard = (text: string, key: string) => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        setCopiedKey(key);
        setTimeout(() => setCopiedKey(null), 2000);
      });
    }
  };

  return (
    <div className="w-full flex-1 flex flex-col bg-transparent text-slate-100 relative selection:bg-blue-500/30 selection:text-white">
      {/* Background ambient lighting */}
      <div 
        className="fixed inset-0 pointer-events-none z-0 overflow-hidden" 
        aria-hidden="true"
      >
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[720px] h-[400px] bg-blue-600/15 rounded-full blur-[140px]" />
        <div className="absolute top-1/3 -left-40 w-[420px] h-[420px] bg-indigo-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-10 -right-40 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[130px]" />
      </div>

      {/* Main Content Area */}
      <div className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10 flex flex-col justify-between">
        {/* Title */}
        <div className="text-center max-w-3xl mx-auto mb-8 sm:mb-12">
          <h1 className="text-4xl sm:text-5xl font-display font-extrabold tracking-tight text-white">
            Sobre nosotros
          </h1>
        </div>

        {/* 5 Lanyards hanging together freely in the same open space (no separate boxes) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 xl:gap-4 w-full mb-12">
          {TEAM_MEMBERS.map((member) => {
            const memberTextures = textures[member.id] || { front: '', back: '' };
            const isCodeCopied = copiedKey === `code-${member.id}`;
            const isEmailCopied = copiedKey === `email-${member.id}`;

            return (
              <div
                key={member.id}
                className="flex flex-col items-center justify-between"
              >
                {/* 3D Lanyard Interactive Stage - Unboxed and hanging loose in open space */}
                <div className="relative h-[380px] sm:h-[410px] xl:h-[440px] w-full flex items-center justify-center overflow-hidden">
                  <Lanyard
                    size={0.6}
                    bandLength={0.5}
                    bandWidth={0.65}
                    bandColor="#111111"
                    cardColor="#0f172a"
                    cornerRadius={0.3}
                    metal="Silver"
                    finish="Glossy"
                    orientation="Portrait"
                    anchor="Center"
                    gravity={1}
                    damping={0.5}
                    elasticity={0.5}
                    breeze={0.5}
                    interactive={true}
                    intro={true}
                    imageFit="Cover"
                    plainBand={false}
                    bandImage="/brand/credirisk-lanyard-strap.png"
                    frontImage={memberTextures.front}
                    backImage={memberTextures.back}
                    className="w-full h-full cursor-grab active:cursor-grabbing"
                  />
                </div>

                {/* Team Member Credential Info - Clean and seamless below */}
                <div className="w-full flex flex-col items-center text-center mt-3 px-2">
                  <h2 className="text-xs sm:text-sm font-bold text-white tracking-tight leading-snug">
                    {member.nombre}
                  </h2>

                  {/* Code Row */}
                  <div className="mt-2 flex items-center justify-center space-x-1.5 text-xs text-slate-400 font-mono">
                    <span className="text-slate-500 text-[11px]">Código:</span>
                    <span className="font-mono font-bold text-sky-300">{member.codigo}</span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(member.codigo, `code-${member.id}`)}
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                      title="Copiar código institucional"
                    >
                      {isCodeCopied ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Email Row */}
                  <div className="mt-1 flex items-center justify-center space-x-1.5 text-xs text-slate-400 font-mono">
                    <a
                      href={`mailto:${member.correo}`}
                      className="text-[11px] font-mono text-slate-400 hover:text-sky-300 transition-colors truncate max-w-[190px]"
                      title={`Enviar correo a ${member.correo}`}
                    >
                      {member.correo}
                    </a>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(member.correo, `email-${member.id}`)}
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors shrink-0 cursor-pointer"
                      title="Copiar correo institucional"
                    >
                      {isEmailCopied ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Feedback indicator if copied */}
                  <div className="mt-1.5 text-center h-4">
                    {(isCodeCopied || isEmailCopied) && (
                      <span className="text-[10px] font-mono text-emerald-400 inline-flex items-center space-x-1 animate-pulse">
                        <Check className="w-2.5 h-2.5" />
                        <span>¡Copiado!</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Global Navigation Actions */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-6 border-t border-white/10">
          <button
            type="button"
            onClick={onBackToHome}
            className="px-4 py-2 rounded-full border border-white/15 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-xs font-semibold backdrop-blur-md transition-colors cursor-pointer"
          >
            Volver al Inicio
          </button>
          <button
            type="button"
            onClick={onOpenEvaluator}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 transition-all cursor-pointer"
          >
            <FileCheck2 className="w-3.5 h-3.5" />
            <span>Abrir Evaluador de Crédito</span>
          </button>
          <button
            type="button"
            onClick={onOpenLab}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-full border border-sky-500/30 bg-sky-950/60 hover:bg-sky-900/60 text-sky-200 text-xs font-semibold shadow-lg shadow-sky-950/40 transition-all cursor-pointer"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            <span>Explorar Laboratorio</span>
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-5xl mx-auto px-6 py-6 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
        <p className="font-sans">
          Redes Neuronales Profundas para Evaluación Crediticia
        </p>
        <p className="font-mono text-slate-500 text-[11px]">
          Universidad Católica de Colombia · 2026
        </p>
      </footer>
    </div>
  );
};

export default AboutUsView;
