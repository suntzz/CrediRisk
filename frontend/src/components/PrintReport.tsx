import React from 'react';
import { BrandLogo } from './BrandLogo';
import { CheckCircle2, XCircle, ShieldCheck } from 'lucide-react';
import type { PredictionResult, ApplicantFormData } from '../types';
import { formatCurrencyDisplay } from '../utils/formatters';

interface PrintReportProps {
  result: PredictionResult;
  applicant: ApplicantFormData;
}

export const PrintReport: React.FC<PrintReportProps> = ({
  result,
  applicant,
}) => {
  const isApto = result.resultado === 'APTO';
  const currentDate = new Date().toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const certId = `CR-CERT-${result.id_solicitud || '172745'}`;

  return (
    <div className="hidden print:block certificate-print-container p-7 bg-white text-slate-900 font-sans border-4 border-double border-slate-300 rounded-lg max-w-3xl mx-auto my-0">
      {/* Encabezado del Certificado */}
      <div className="flex items-center justify-between border-b-2 border-slate-900 pb-4 mb-6">
        <div className="flex items-center">
          <BrandLogo size="md" variant="light" className="shrink-0" />
          <div className="ml-1">
            <div className="flex items-baseline">
              <span className="font-display font-extrabold text-2xl tracking-tight text-slate-950 leading-none -ml-1.5">
                rediRisk
              </span>
            </div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 mt-1">
              Sistema de Evaluación de Riesgo Financiero
            </div>
          </div>
        </div>
        <div className="text-right font-mono text-xs text-slate-600">
          <div><strong>Certificado No.:</strong> {certId}</div>
          <div><strong>Fecha de Emisión:</strong> {currentDate}</div>
        </div>
      </div>

      {/* Título del Certificado */}
      <div className="text-center mb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-950 uppercase mb-1">
          Certificado Oficial de Dictamen Crediticio
        </h1>
        <p className="text-xs text-slate-600">
          Inferencia analítica automatizada mediante Redes Neuronales Profundas
        </p>
      </div>

      {/* Datos Clave de la Solicitud */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-5 text-xs">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-2.5 gap-x-4">
          <div>
            <span className="text-slate-500 block text-[11px]">Número de Solicitud:</span>
            <span className="font-semibold text-slate-900 text-sm">#{result.id_solicitud}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Monto Solicitado:</span>
            <span className="font-semibold text-slate-900 text-sm font-mono">
              {formatCurrencyDisplay(applicant.monto_solicitado || 0, { showCode: true })}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Plazo de Financiamiento:</span>
            <span className="font-semibold text-slate-900 text-sm">{applicant.plazo_meses} meses</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Línea de Crédito:</span>
            <span className="font-semibold text-slate-900">{applicant.linea_negocio || 'Crédito de Consumo'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Ingreso Mensual Registrado:</span>
            <span className="font-semibold text-slate-900 text-sm font-mono">
              {formatCurrencyDisplay(applicant.ingreso_mensual || 0, { showCode: true })}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Score Crediticio Evaluado:</span>
            <span className="font-semibold text-slate-900">{applicant.score_crediticio} pts</span>
          </div>
        </div>
      </div>

      {/* DICTAMEN OFICIAL CENTRAL */}
      <div
        className={`p-5 rounded-xl border-2 mb-5 text-center ${
          isApto
            ? 'border-emerald-600 bg-emerald-50/80 text-emerald-950'
            : 'border-rose-600 bg-rose-50/80 text-rose-950'
        }`}
      >
        <div className="flex items-center justify-center space-x-2.5 mb-2">
          {isApto ? (
            <CheckCircle2 className="w-7 h-7 text-emerald-600 shrink-0" />
          ) : (
            <XCircle className="w-7 h-7 text-rose-600 shrink-0" />
          )}
          <span className="text-2xl font-black tracking-wide">
            {isApto ? 'DICTAMEN: APTO PARA CRÉDITO' : 'DICTAMEN: NO APTO PARA CRÉDITO'}
          </span>
        </div>

        <p className="text-xs sm:text-sm font-medium mt-2 max-w-xl mx-auto leading-relaxed">
          {isApto
            ? 'Se certifica formalmente que el solicitante cumple con los criterios de solvencia, capacidad de pago y políticas de riesgo analizadas por el ensamble de redes neuronales profundas.'
            : 'Se certifica que la solicitud no alcanza los umbrales mínimos de viabilidad crediticia requeridos por el modelo de riesgo financiero para el otorgamiento del crédito.'}
        </p>

        <div className="mt-3 pt-2.5 border-t border-slate-300/60 inline-flex items-center space-x-4 text-xs font-mono">
          <span>
            <strong>Probabilidad de Cumplimiento:</strong> {(result.probabilidad_apto * 100).toFixed(2)}%
          </span>
          <span>|</span>
          <span>
            <strong>Umbral Requerido:</strong> 50.00%
          </span>
        </div>
      </div>

      {/* Certificación y Firmas */}
      <div className="mt-5 pt-4 border-t border-slate-300 text-xs text-slate-600">
        <div className="flex items-center space-x-2 mb-6 text-[11px] text-slate-500 justify-center">
          <ShieldCheck className="w-4 h-4 text-slate-700" />
          <span>Certificación respaldada por motor neuronal ensemble validado con 49,650 casos test.</span>
        </div>

        <div className="grid grid-cols-2 gap-10 pt-3">
          <div className="text-center">
            <div className="border-t border-slate-400 pt-2 font-semibold text-slate-900">
              Comité de Evaluación de Crédito
            </div>
            <div className="text-[11px] text-slate-500">CrediRisk Financial Technologies</div>
          </div>
          <div className="text-center">
            <div className="border-t border-slate-400 pt-2 font-semibold text-slate-900">
              Validación y Dictamen AI
            </div>
            <div className="text-[11px] text-slate-500">Motor Deep Learning Ensemble</div>
          </div>
        </div>

        <div className="mt-3 text-center text-[10px] text-slate-400 font-mono">
          Este documento es un certificado oficial emitido por CrediRisk · Validez técnica y académica · Universidad Católica de Colombia 2026
        </div>
      </div>
    </div>
  );
};

export default PrintReport;
