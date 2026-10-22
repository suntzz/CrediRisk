import React, { useLayoutEffect, useRef, useState } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  RotateCcw, 
  Sparkles, 
  AlertCircle,
  CheckCircle2,
  XCircle,
  Calculator,
  User,
  DollarSign,
  History,
  Briefcase,
  FileText,
  Printer,
  ShieldCheck,
  TrendingUp,
  Info,
  AlertTriangle
} from 'lucide-react';
import { PrintReport } from './PrintReport';
import { Stepper, Step } from './Stepper';
import { FormattedCurrencyInput } from './FormattedCurrencyInput';
import { formatCurrencyDisplay } from '../utils/formatters';
import { useTheme } from '../context/ThemeContext';
import { predictApplicant, fetchSampleApplicant } from '../services/api';
import { EMPTY_FORM_STATE } from '../types';
import type { ApplicantFormData, ApplicantFormState, PredictionResult } from '../types';

interface EvaluatorViewProps {
  onBackToHome: () => void;
  onOpenLab: () => void;
  onOpenAbout: () => void;
  defaultData?: ApplicantFormData | ApplicantFormState;
}

const TOTAL_STEPS = 5;

const STEP_LABELS = [
  { step: 1, title: 'Datos Personales', subtitle: 'Perfil e identidad' },
  { step: 2, title: 'Capacidad Financiera', subtitle: 'Flujos y condiciones' },
  { step: 3, title: 'Historial Crediticio', subtitle: 'Buró y puntualidad' },
  { step: 4, title: 'Perfil Laboral', subtitle: 'Ocupación y contrato' },
  { step: 5, title: 'Diagnóstico Final', subtitle: 'Revisión y cálculo' },
];

const getFactorDisplayTitle = (factor: { variable: string; impacto: string }): string => {
  const normVar = factor.variable.toLowerCase();
  if (normVar.includes('cobertura')) {
    return factor.impacto === 'negativo'
      ? 'Cobertura de cuota insuficiente'
      : 'Cobertura de cuota adecuada';
  }
  if (normVar.includes('score')) {
    return factor.impacto === 'negativo'
      ? 'Score crediticio bajo'
      : 'Score crediticio favorable';
  }
  if (normVar.includes('endeudamiento')) {
    return factor.impacto === 'negativo'
      ? 'Nivel de endeudamiento elevado'
      : 'Nivel de endeudamiento saludable';
  }
  if (normVar.includes('mora')) {
    return factor.impacto === 'negativo'
      ? 'Historial de mora con retrasos'
      : 'Historial crediticio al día';
  }
  return factor.variable;
};

const parseComparisonValue = (val: string) => {
  if (val.includes(' vs ')) {
    const parts = val.split(' vs ');
    return {
      isComparison: true,
      first: parts[0]?.trim() || '',
      second: parts[1]?.trim() || '',
    };
  }
  return {
    isComparison: false,
    first: val,
    second: '',
  };
};

export const EvaluatorView: React.FC<EvaluatorViewProps> = ({
  onBackToHome: _onBackToHome,
  onOpenLab,
  onOpenAbout: _onOpenAbout,
  defaultData,
}) => {
  const { isDark } = useTheme();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [formData, setFormData] = useState<ApplicantFormState>(() => {
    if (defaultData) {
      return { ...defaultData } as ApplicantFormState;
    }
    return { ...EMPTY_FORM_STATE };
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [lastEvaluatedApplicant, setLastEvaluatedApplicant] = useState<ApplicantFormData | null>(null);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const formTopRef = useRef<HTMLDivElement>(null);
  const isFirstFormRender = useRef(true);

  // Al cambiar de etapa, mostrar un error o el dictamen, si el inicio del formulario quedó fuera de vista
  // se lleva a la vista (antes el banner de error empujaba "Continuar" fuera de pantalla).
  useLayoutEffect(() => {
    if (isFirstFormRender.current) {
      isFirstFormRender.current = false;
      return;
    }
    const formTop = formTopRef.current;
    if (!formTop) return;
    const top = formTop.getBoundingClientRect().top;
    const offset = parseFloat(getComputedStyle(formTop).scrollMarginTop) || 0;
    if (top < offset) {
      formTop.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }
  }, [currentStep, errorMsg, prediction]);

  // Field change handler: conserva valores vacíos como '' y no los fuerza a 0
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (value === '') {
      setFormData(prev => ({ ...prev, [name]: '' }));
    } else if (type === 'number') {
      const parsed = parseFloat(value);
      setFormData(prev => ({ ...prev, [name]: isNaN(parsed) ? '' : parsed }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }

    // Limpiar error en tiempo real si el usuario modifica el campo
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
    if (errorMsg) {
      setErrorMsg(null);
    }
  };

  // Helper auto-calculations (operan sobre valores numéricos puros en COP)
  const handleAutoDisposableIncome = () => {
    if (formData.ingreso_mensual === '' || Number(formData.ingreso_mensual) <= 0) {
      setFieldErrors(prev => ({
        ...prev,
        ingreso_mensual: 'Ingrese un ingreso mensual mayor a 0 para auto-calcular.',
      }));
      setErrorMsg('Ingrese un ingreso mensual válido para auto-calcular el ingreso disponible.');
      return;
    }
    const income = Number(formData.ingreso_mensual);
    const obligations = formData.obligaciones_mensuales === '' ? 0 : Number(formData.obligaciones_mensuales);
    const disp = income - obligations;
    setFormData(prev => ({ ...prev, ingreso_disponible: Math.round(disp) }));
    setFieldErrors(prev => {
      const next = { ...prev };
      delete next.ingreso_disponible;
      return next;
    });
    setErrorMsg(null);
  };

  const handleAutoDebtRatio = () => {
    if (formData.ingreso_mensual === '' || Number(formData.ingreso_mensual) <= 0) {
      setFieldErrors(prev => ({
        ...prev,
        ingreso_mensual: 'Ingrese un ingreso mensual mayor a 0 para auto-calcular.',
      }));
      setErrorMsg('Ingrese un ingreso mensual mayor a 0 para auto-calcular el nivel de endeudamiento.');
      return;
    }
    const income = Number(formData.ingreso_mensual);
    const obligations = formData.obligaciones_mensuales === '' ? 0 : Number(formData.obligaciones_mensuales);
    const ratio = (obligations / income) * 100;
    setFormData(prev => ({ ...prev, nivel_endeudamiento_pct: parseFloat(ratio.toFixed(2)) }));
    setFieldErrors(prev => {
      const next = { ...prev };
      delete next.nivel_endeudamiento_pct;
      return next;
    });
    setErrorMsg(null);
  };

  const handleAutoInstallment = () => {
    const missing: string[] = [];
    if (formData.monto_solicitado === '' || Number(formData.monto_solicitado) <= 0) missing.push('Monto Solicitado');
    if (formData.plazo_meses === '' || Number(formData.plazo_meses) <= 0) missing.push('Plazo');
    if (formData.tasa_interes_ea === '' || Number(formData.tasa_interes_ea) < 0) missing.push('Tasa de Interés');

    if (missing.length > 0) {
      setErrorMsg(`Para auto-estimar la cuota se requieren valores válidos en: ${missing.join(', ')}.`);
      return;
    }

    const principal = Number(formData.monto_solicitado);
    const months = Number(formData.plazo_meses);
    const rateEA = Number(formData.tasa_interes_ea) / 100;

    let installment = 0;
    if (rateEA > 0) {
      const monthlyRate = Math.pow(1 + rateEA, 1 / 12) - 1;
      installment = (principal * monthlyRate) / (1 - Math.pow(1 + monthlyRate, -months));
    } else {
      installment = principal / months;
    }

    setFormData(prev => ({ ...prev, cuota_estimada: Math.round(installment) }));
    setFieldErrors(prev => {
      const next = { ...prev };
      delete next.cuota_estimada;
      return next;
    });
    setErrorMsg(null);
  };

  // Sample data loader
  const handleLoadSample = async () => {
    setLoadingSample(true);
    setErrorMsg(null);
    setFieldErrors({});
    try {
      const sample = await fetchSampleApplicant();
      setFormData({
        ...sample,
        model_type: 'ensemble',
      });
    } catch {
      setFormData({
        id_solicitud: 172745,
        edad: 43.9,
        ingreso_mensual: 202500.0,
        obligaciones_mensuales: 153454.09,
        estado_civil: 'Single / not married',
        ingreso_disponible: 13522.91,
        monto_solicitado: 835380.0,
        plazo_meses: 48.0,
        cuota_estimada: 35523.0,
        tasa_interes_ea: 49.31,
        nivel_endeudamiento_pct: 93.32,
        score_crediticio: 585.0,
        numero_creditos_activos: 2.0,
        saldo_total_creditos: 2619045.0,
        numero_cuotas_mora: 0.0,
        dias_maximo_mora: 0.0,
        porcentaje_pagos_oportunos: 100.0,
        antiguedad_laboral_anios: 7.17,
        patrimonio_indice: 4,
        antiguedad_cliente_anios: 7.74,
        linea_negocio: 'Cash loans',
        tipo_contrato: 'Working',
        personas_a_cargo: 1,
        tipo_vivienda: 'House / apartment',
        model_type: 'ensemble',
      });
    } finally {
      setLoadingSample(false);
    }
  };

  // Reset handler
  const handleReset = () => {
    setFormData({ ...EMPTY_FORM_STATE });
    setPrediction(null);
    setLastEvaluatedApplicant(null);
    setCurrentStep(1);
    setErrorMsg(null);
    setFieldErrors({});
  };

  // Step validation
  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};

    if (step === 1) {
      if (formData.edad === '') {
        errors.edad = 'La edad del solicitante es obligatoria.';
      } else {
        const val = Number(formData.edad);
        if (isNaN(val) || val < 18 || val > 95) {
          errors.edad = 'La edad debe estar comprendida entre 18 y 95 años.';
        }
      }

      if (!formData.estado_civil || formData.estado_civil.trim() === '') {
        errors.estado_civil = 'Seleccione el estado civil del solicitante.';
      }

      if (formData.personas_a_cargo === '') {
        errors.personas_a_cargo = 'El número de dependientes es obligatorio (ingrese 0 si no tiene).';
      } else {
        const val = Number(formData.personas_a_cargo);
        if (isNaN(val) || val < 0 || val > 15) {
          errors.personas_a_cargo = 'El número de personas a cargo debe estar entre 0 y 15.';
        }
      }

      if (!formData.tipo_vivienda || formData.tipo_vivienda.trim() === '') {
        errors.tipo_vivienda = 'Seleccione el tipo de vivienda del solicitante.';
      }
    } else if (step === 2) {
      if (formData.ingreso_mensual === '') {
        errors.ingreso_mensual = 'El ingreso mensual es obligatorio.';
      } else {
        const val = Number(formData.ingreso_mensual);
        if (isNaN(val) || val <= 0) {
          errors.ingreso_mensual = 'El ingreso mensual debe ser mayor a 0.';
        }
      }

      if (formData.obligaciones_mensuales !== '') {
        const val = Number(formData.obligaciones_mensuales);
        if (isNaN(val) || val < 0) {
          errors.obligaciones_mensuales = 'Las obligaciones mensuales no pueden ser negativas.';
        }
      }

      if (formData.ingreso_disponible === '') {
        errors.ingreso_disponible = 'El ingreso disponible es obligatorio (puede auto-calcularlo).';
      } else {
        const val = Number(formData.ingreso_disponible);
        if (isNaN(val)) {
          errors.ingreso_disponible = 'Ingrese un valor numérico válido para el ingreso disponible.';
        }
      }

      if (formData.nivel_endeudamiento_pct === '') {
        errors.nivel_endeudamiento_pct = 'El nivel de endeudamiento es obligatorio.';
      } else {
        const val = Number(formData.nivel_endeudamiento_pct);
        if (isNaN(val) || val < 0 || val > 1000) {
          errors.nivel_endeudamiento_pct = 'El nivel de endeudamiento debe ser mayor o igual a 0%.';
        }
      }

      if (formData.monto_solicitado === '') {
        errors.monto_solicitado = 'El monto solicitado es obligatorio.';
      } else {
        const val = Number(formData.monto_solicitado);
        if (isNaN(val) || val <= 0) {
          errors.monto_solicitado = 'El monto solicitado debe ser mayor a 0.';
        }
      }

      if (formData.plazo_meses === '') {
        errors.plazo_meses = 'El plazo del crédito es obligatorio.';
      } else {
        const val = Number(formData.plazo_meses);
        if (isNaN(val) || val < 1 || val > 120) {
          errors.plazo_meses = 'El plazo debe situarse entre 1 y 120 meses.';
        }
      }

      if (formData.tasa_interes_ea === '') {
        errors.tasa_interes_ea = 'La tasa de interés es obligatoria.';
      } else {
        const val = Number(formData.tasa_interes_ea);
        if (isNaN(val) || val < 0 || val > 150) {
          errors.tasa_interes_ea = 'La tasa de interés debe situarse entre 0% y 150% E.A.';
        }
      }

      if (formData.cuota_estimada === '') {
        errors.cuota_estimada = 'La cuota estimada es obligatoria (puede auto-estimarla).';
      } else {
        const val = Number(formData.cuota_estimada);
        if (isNaN(val) || val <= 0) {
          errors.cuota_estimada = 'La cuota estimada debe ser un monto mayor a 0.';
        }
      }
    } else if (step === 3) {
      if (formData.score_crediticio === '') {
        errors.score_crediticio = 'El score crediticio es obligatorio.';
      } else {
        const val = Number(formData.score_crediticio);
        if (isNaN(val) || val < 0 || val > 1000) {
          errors.score_crediticio = 'El score crediticio debe estar entre 0 y 1000 puntos.';
        }
      }

      if (formData.numero_creditos_activos !== '') {
        const val = Number(formData.numero_creditos_activos);
        if (isNaN(val) || val < 0) {
          errors.numero_creditos_activos = 'El número de créditos activos debe ser mayor o igual a 0.';
        }
      }

      if (formData.saldo_total_creditos !== '') {
        const val = Number(formData.saldo_total_creditos);
        if (isNaN(val) || val < 0) {
          errors.saldo_total_creditos = 'El saldo total de deuda debe ser mayor o igual a 0.';
        }
      }

      if (formData.numero_cuotas_mora !== '') {
        const val = Number(formData.numero_cuotas_mora);
        if (isNaN(val) || val < 0) {
          errors.numero_cuotas_mora = 'El número de cuotas en mora debe ser mayor o igual a 0.';
        }
      }

      if (formData.dias_maximo_mora === '') {
        errors.dias_maximo_mora = 'Los días de mora son obligatorios (ingrese 0 si está al día).';
      } else {
        const val = Number(formData.dias_maximo_mora);
        if (isNaN(val) || val < 0) {
          errors.dias_maximo_mora = 'Los días máximos de mora no pueden ser negativos.';
        }
      }

      if (formData.porcentaje_pagos_oportunos !== '') {
        const val = Number(formData.porcentaje_pagos_oportunos);
        if (isNaN(val) || val < 0 || val > 100) {
          errors.porcentaje_pagos_oportunos = 'El porcentaje de pagos oportunos debe estar entre 0% y 100%.';
        }
      }
    } else if (step === 4) {
      if (!formData.linea_negocio || formData.linea_negocio.trim() === '') {
        errors.linea_negocio = 'Seleccione la línea de negocio del crédito.';
      }

      if (!formData.tipo_contrato || formData.tipo_contrato.trim() === '') {
        errors.tipo_contrato = 'Seleccione el tipo de contrato u ocupación.';
      }

      if (formData.antiguedad_laboral_anios !== '') {
        const val = Number(formData.antiguedad_laboral_anios);
        if (isNaN(val) || val < 0 || val > 60) {
          errors.antiguedad_laboral_anios = 'La antigüedad laboral debe estar entre 0 y 60 años.';
        }
      }

      if (formData.antiguedad_cliente_anios !== '') {
        const val = Number(formData.antiguedad_cliente_anios);
        if (isNaN(val) || val < 0 || val > 60) {
          errors.antiguedad_cliente_anios = 'La antigüedad como cliente debe estar entre 0 y 60 años.';
        }
      }

      if (formData.patrimonio_indice === '') {
        errors.patrimonio_indice = 'El índice patrimonial es obligatorio.';
      } else {
        const val = Number(formData.patrimonio_indice);
        if (isNaN(val) || val < 0 || val > 10) {
          errors.patrimonio_indice = 'El índice patrimonial debe estar en la escala de 0 a 10.';
        }
      }
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(prev => ({ ...prev, ...errors }));
      setErrorMsg('Por favor complete o corrija los campos requeridos señalados en rojo antes de continuar.');
      return false;
    }

    return true;
  };

  const handleNextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(TOTAL_STEPS, prev + 1));
    }
  };

  const handlePrevStep = () => {
    setErrorMsg(null);
    setCurrentStep(prev => Math.max(1, prev - 1));
  };

  // Helper styles para inputs y selects con validación visual
  const getInputClassName = (name: string, isMono = false, isHero = false) => {
    const hasError = !!fieldErrors[name];
    const base = isHero
      ? 'w-full px-4 py-2.5 text-base font-bold bg-white dark:bg-slate-900 rounded-xl text-slate-900 dark:text-white outline-none transition'
      : 'w-full px-3.5 py-2.5 text-sm bg-white dark:bg-slate-900 rounded-xl text-slate-900 dark:text-white outline-none transition';
    const font = isMono ? 'font-mono' : 'font-sans';
    const border = hasError
      ? 'border-2 border-rose-500 dark:border-rose-500 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20'
      : 'border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500';
    return `${base} ${font} ${border}`;
  };

  const getSelectClassName = (name: string) => {
    const hasError = !!fieldErrors[name];
    const base = 'w-full px-3.5 py-2.5 text-sm bg-white dark:bg-slate-900 rounded-xl text-slate-900 dark:text-white outline-none transition';
    const border = hasError
      ? 'border-2 border-rose-500 dark:border-rose-500 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20'
      : 'border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500';
    return `${base} ${border}`;
  };

  // Submit inference con validación exhaustiva previa
  const handleExecuteInference = async () => {
    setErrorMsg(null);
    for (let step = 1; step <= 4; step++) {
      if (!validateStep(step)) {
        setCurrentStep(step);
        setErrorMsg(`La etapa ${step} contiene campos pendientes o no válidos. Por favor verifíquelos.`);
        return;
      }
    }

    const payload: ApplicantFormData = {
      id_solicitud: typeof formData.id_solicitud === 'number' ? formData.id_solicitud : 999001,
      edad: Number(formData.edad),
      estado_civil: formData.estado_civil.trim(),
      personas_a_cargo: Number(formData.personas_a_cargo),
      tipo_vivienda: formData.tipo_vivienda.trim(),

      ingreso_mensual: Number(formData.ingreso_mensual),
      obligaciones_mensuales: formData.obligaciones_mensuales === '' ? undefined : Number(formData.obligaciones_mensuales),
      ingreso_disponible: Number(formData.ingreso_disponible),
      monto_solicitado: Number(formData.monto_solicitado),
      plazo_meses: Number(formData.plazo_meses),
      cuota_estimada: Number(formData.cuota_estimada),
      tasa_interes_ea: Number(formData.tasa_interes_ea),
      nivel_endeudamiento_pct: Number(formData.nivel_endeudamiento_pct),

      score_crediticio: Number(formData.score_crediticio),
      numero_creditos_activos: formData.numero_creditos_activos === '' ? undefined : Number(formData.numero_creditos_activos),
      saldo_total_creditos: formData.saldo_total_creditos === '' ? undefined : Number(formData.saldo_total_creditos),
      numero_cuotas_mora: formData.numero_cuotas_mora === '' ? undefined : Number(formData.numero_cuotas_mora),
      dias_maximo_mora: Number(formData.dias_maximo_mora),
      porcentaje_pagos_oportunos: formData.porcentaje_pagos_oportunos === '' ? undefined : Number(formData.porcentaje_pagos_oportunos),

      antiguedad_laboral_anios: formData.antiguedad_laboral_anios === '' ? undefined : Number(formData.antiguedad_laboral_anios),
      patrimonio_indice: Number(formData.patrimonio_indice),
      antiguedad_cliente_anios: formData.antiguedad_cliente_anios === '' ? undefined : Number(formData.antiguedad_cliente_anios),
      linea_negocio: formData.linea_negocio.trim(),
      tipo_contrato: formData.tipo_contrato.trim(),

      model_type: 'ensemble',
    };

    setIsLoading(true);
    try {
      const res = await predictApplicant(payload);
      setLastEvaluatedApplicant(payload);
      setPrediction(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al ejecutar la inferencia del modelo.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full flex flex-col bg-transparent text-slate-100 transition-colors">
      {/* Main Container */}
      <div ref={formTopRef} className="flex-1 max-w-4xl w-full mx-auto px-6 py-6 sm:py-8 scroll-mt-20 print:hidden">
        {/* Error notification */}
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs flex items-start justify-between shadow-sm animate-in fade-in duration-150">
            <div className="flex items-start space-x-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
              <div>
                <strong className="block font-semibold">Validación requerida:</strong>
                <span>{errorMsg}</span>
              </div>
            </div>
            <button onClick={() => setErrorMsg(null)} className="text-rose-500 hover:text-rose-700 ml-3">✕</button>
          </div>
        )}

        {/* Prediction Ready: Quantitative Certificate Verdict */}
        {prediction ? (
          <div className="bg-white dark:bg-[#0F172A]/90 rounded-2xl border border-slate-200/90 dark:border-slate-800/90 shadow-sm p-6 sm:p-8 space-y-8 animate-in fade-in duration-200">
            {/* Certificate Top Banner */}
            <div className="border-b border-slate-200/80 dark:border-slate-800/80 pb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2 text-xs font-mono text-slate-500 dark:text-slate-400 mb-1">
                  <span>EXPEDIENTE TÉCNICO #{prediction.id_solicitud}</span>
                  <span>·</span>
                  <span>{new Date().toLocaleDateString('es-CO')}</span>
                </div>
                <h1 className="text-xl sm:text-2xl font-display font-bold text-slate-900 dark:text-white tracking-tight">
                  Dictamen de Inferencia Crediticia
                </h1>
              </div>

              <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800/80 text-[11px] font-mono text-slate-700 dark:text-slate-300 border border-slate-200/70 dark:border-slate-700/70">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                <span>Modelo: Ensemble Top-3 Diverso</span>
              </div>
            </div>

            {/* Verdict Centerpiece */}
            <div className="text-center max-w-xl mx-auto py-2">
              <span className="text-[11px] uppercase tracking-widest text-slate-500 dark:text-slate-400 font-mono block mb-3">
                Resultado Oficial del Algoritmo
              </span>

              {/* Classification Pill */}
              <div className="flex items-center justify-center mb-6">
                {prediction.resultado === 'APTO' ? (
                  <div className="inline-flex items-center space-x-3 px-6 py-3 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 font-display font-bold text-base shadow-sm">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    <span>Apto para crédito</span>
                  </div>
                ) : (
                  <div className="inline-flex items-center space-x-3 px-6 py-3 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-400 font-display font-bold text-base shadow-sm">
                    <XCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                    <span>No apto para crédito</span>
                  </div>
                )}
              </div>

              {/* Probability Number */}
              <div className="mb-6">
                <span className="text-xs text-slate-500 dark:text-slate-400 block mb-1">
                  Probabilidad calculada de cumplimiento crediticio P(Apto)
                </span>
                <div className="text-5xl sm:text-6xl font-mono font-bold tracking-tight text-slate-900 dark:text-white">
                  {(prediction.probabilidad_apto * 100).toFixed(2)}%
                </div>
              </div>

              {/* Calibrated Probability Gauge */}
              <div className="space-y-2 max-w-md mx-auto">
                <div className="relative pt-6 pb-2">
                  {/* Gauge Track */}
                  <div className="h-3 w-full rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden relative">
                    {/* El color sigue al dictamen; se rellena con scaleX (transform) en lugar de animar el ancho */}
                    <div 
                      className={`credirisk-gauge-fill h-full w-full origin-left ${
                        prediction.resultado === 'APTO' ? 'bg-emerald-500' : 'bg-rose-500'
                      }`}
                      style={{ transform: `scaleX(${Math.min(1, Math.max(0, prediction.probabilidad_apto))})` }}
                    />
                  </div>

                  {/* 50% Threshold marker */}
                  <div 
                    className="absolute top-2 bottom-0 w-0.5 bg-slate-900 dark:bg-white z-10 flex flex-col items-center"
                    style={{ left: '50%' }}
                  >
                    <span className="absolute -top-4 text-[10px] font-mono text-slate-500 dark:text-slate-400 whitespace-nowrap">
                      Umbral 50%
                    </span>
                  </div>
                </div>

                <div className="flex justify-between text-[11px] font-mono text-slate-500 dark:text-slate-400">
                  <span>0% (Riesgo Crítico)</span>
                  <span>100% (Perfil Óptimo)</span>
                </div>
              </div>

              {/* Scientific Interpretation */}
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed max-w-lg mx-auto mt-6">
                {prediction.resultado === 'APTO'
                  ? `La probabilidad estimada (${(prediction.probabilidad_apto * 100).toFixed(2)}%) supera el umbral estricto de decisión (50.00%). El perfil financiero y de buró se clasifica dentro de la categoría de cumplimiento.`
                  : `La probabilidad estimada (${(prediction.probabilidad_apto * 100).toFixed(2)}%) se sitúa por debajo del umbral estricto de decisión (50.00%). El perfil refleja factores de riesgo que comprometen la viabilidad crediticia.`}
              </p>
            </div>

            {/* Relevant Factors Breakdown */}
            {prediction.factores_relevantes && prediction.factores_relevantes.length > 0 && (
              <div className="border-t border-slate-200/80 dark:border-slate-800/80 pt-6">
                <div className="flex items-center space-x-2 text-xs font-mono font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-4">
                  <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span>Factores Determinantes Identificados por el Modelo</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {prediction.factores_relevantes.map((factor, idx) => {
                    const comparison = parseComparisonValue(factor.valor);
                    const displayTitle = getFactorDisplayTitle(factor);
                    const isNegative = factor.impacto === 'negativo';
                    const isPositive = factor.impacto === 'positivo';

                    return (
                      <div 
                        key={idx} 
                        className={`p-4 sm:p-5 rounded-2xl border transition-all flex flex-col justify-between gap-3.5 ${
                          isNegative
                            ? 'bg-rose-50/70 dark:bg-rose-950/25 border-rose-200/80 dark:border-rose-900/60'
                            : isPositive
                            ? 'bg-emerald-50/70 dark:bg-emerald-950/25 border-emerald-200/80 dark:border-emerald-900/60'
                            : 'bg-slate-50/80 dark:bg-slate-900/60 border-slate-200/80 dark:border-slate-800/80'
                        }`}
                      >
                        {/* Cabecera del factor: Icono, Título y Distintivo */}
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center space-x-2.5">
                            <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                              isNegative
                                ? 'bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400'
                                : isPositive
                                ? 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400'
                                : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                            }`}>
                              {isNegative ? (
                                <AlertTriangle className="w-4 h-4" />
                              ) : isPositive ? (
                                <TrendingUp className="w-4 h-4" />
                              ) : (
                                <Info className="w-4 h-4" />
                              )}
                            </div>
                            <h4 className="font-display font-bold text-sm tracking-tight text-slate-900 dark:text-white">
                              {displayTitle}
                            </h4>
                          </div>

                          <span
                            className={`px-2.5 py-0.5 rounded-md text-[10px] font-sans font-semibold uppercase tracking-wider shrink-0 ${
                              isNegative
                                ? 'bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-200'
                                : isPositive
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200'
                                : 'bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200'
                            }`}
                          >
                            {isNegative ? 'Desfavorable' : isPositive ? 'Favorable' : 'Neutro'}
                          </span>
                        </div>

                        {/* Descripción detallada */}
                        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans">
                          {factor.detalle}
                        </p>

                        {/* Valores e indicadores financieros bien espaciados y alineados */}
                        {comparison.isComparison ? (
                          <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800/60">
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 shadow-2xs">
                                <span className="text-[11px] font-sans text-slate-500 dark:text-slate-400">
                                  Disponible:
                                </span>
                                <span className="font-mono text-xs font-bold text-slate-900 dark:text-white tabular-nums">
                                  {comparison.first.replace(' disponible', '')}
                                </span>
                              </div>

                              <span className="text-xs font-sans text-slate-400 dark:text-slate-500 font-medium">
                                vs
                              </span>

                              <div className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border shadow-2xs ${
                                isNegative 
                                  ? 'bg-rose-100/70 dark:bg-rose-950/60 border-rose-200 dark:border-rose-900/70 text-rose-900 dark:text-rose-200'
                                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700/80 text-slate-900 dark:text-white'
                              }`}>
                                <span className="text-[11px] font-sans text-slate-500 dark:text-slate-400">
                                  Cuota estimada:
                                </span>
                                <span className="font-mono text-xs font-bold tabular-nums">
                                  {comparison.second.replace(' cuota', '')}
                                </span>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between text-xs">
                            <span className="text-[11px] font-sans text-slate-500 dark:text-slate-400">
                              Métrica observada:
                            </span>
                            <span className="font-mono text-xs font-bold text-slate-900 dark:text-white tabular-nums px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 shadow-2xs">
                              {factor.valor}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Evaluated Variables Summary Grid */}
            <div className="bg-slate-50 dark:bg-[#0B1220]/60 rounded-xl p-5 border border-slate-200/80 dark:border-slate-800/80 text-xs">
              <span className="font-mono text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-3 uppercase tracking-wider">
                Resumen del Perfil Registrado
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-slate-600 dark:text-slate-300 font-mono">
                <div>
                  <span className="text-[10px] text-slate-400 block font-sans">Score Buró</span>
                  <strong className="text-slate-900 dark:text-white">{formData.score_crediticio} pts</strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-sans">Monto Solicitado</span>
                  <strong className="text-slate-900 dark:text-white font-mono">
                    {formatCurrencyDisplay(formData.monto_solicitado)}
                  </strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-sans">Nivel Endeudamiento</span>
                  <strong className="text-slate-900 dark:text-white">{formData.nivel_endeudamiento_pct}%</strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-sans">Días Máx Mora</span>
                  <strong className="text-slate-900 dark:text-white">{formData.dias_maximo_mora} días</strong>
                </div>
              </div>
            </div>

            {/* Actions Toolbar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
              <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={() => setPrediction(null)}
                  className="px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                >
                  Modificar datos actuales
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                >
                  Nuevo solicitante
                </button>
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                  title="Imprimir Certificado Oficial en PDF"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Imprimir Certificado</span>
                </button>
              </div>

              <button
                type="button"
                onClick={onOpenLab}
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
              >
                <span>Inspeccionar en el Laboratorio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Academic disclaimer */}
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed text-center">
              Aviso metodológico: Este sistema es un prototipo académico basado en redes neuronales entrenadas sobre una muestra experimental balanceada (50% aptos / 50% no aptos). La predicción probabilística refleja correlaciones estadísticas multivariadas y no constituye una aprobación crediticia bancaria vinculante.
            </div>
          </div>
        ) : (
          /* Multi-Step Quantitative Form */
          <div className="bg-white dark:bg-[#0F172A]/90 rounded-2xl border border-slate-200/90 dark:border-slate-800/90 shadow-sm overflow-hidden">
            {/* Form Top Toolbar */}
            <div className="px-6 py-4 border-b border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between gap-4 bg-slate-50/70 dark:bg-slate-900/50">
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-mono font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                  Etapa {currentStep} de {TOTAL_STEPS}
                </span>
                <span className="text-slate-300 dark:text-slate-700">·</span>
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  {STEP_LABELS[currentStep - 1].title}
                </span>
                <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">·</span>
                <span className="text-xs font-normal text-slate-500 dark:text-slate-400 hidden sm:inline">
                  {STEP_LABELS[currentStep - 1].subtitle}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleLoadSample}
                  disabled={loadingSample}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-colors disabled:opacity-50"
                  title="Cargar perfil de prueba predeterminado"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-cyan-400" />
                  <span>{loadingSample ? 'Cargando...' : 'Cargar Ejemplo'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                  title="Restablecer valores del formulario"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* React Bits Visual Stepper Integration */}
            <div className="p-6 sm:p-8">
              <Stepper
                step={currentStep}
                onStepChange={(targetStep) => {
                  // Only allow retroceding via indicators; advancing is strictly gated behind "Continuar"
                  if (targetStep < currentStep) {
                    setCurrentStep(targetStep);
                    setErrorMsg(null);
                  }
                }}
                indicator="bars"
                allowAdvanceViaIndicators={false}
                linear={true}
                frame={false}
                width="100%"
                theme={isDark ? 'dark' : 'light'}
                accentColor={isDark ? '#38BDF8' : '#2563EB'}
                showFooter={false}
                className="w-full"
              >
                <Step title="Datos Personales" description="Perfil e identidad">
                  <div className="space-y-6 animate-in fade-in duration-150 pt-2">
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800/60">
                    <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <span>01. Parámetros personales y situación familiar</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Edad del Solicitante (años) <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="edad"
                        step="0.1"
                        min="18"
                        max="95"
                        value={formData.edad === '' ? '' : formData.edad}
                        onChange={handleChange}
                        className={getInputClassName('edad', true)}
                        placeholder="Ej. 43.9"
                      />
                      {fieldErrors.edad && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.edad}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Estado Civil <span className="text-rose-500">*</span>
                      </label>
                      <select
                        name="estado_civil"
                        value={formData.estado_civil}
                        onChange={handleChange}
                        className={getSelectClassName('estado_civil')}
                      >
                        <option value="">Seleccione una opción...</option>
                        <option value="Single / not married">Soltero(a) / No casado</option>
                        <option value="Married">Casado(a)</option>
                        <option value="Civil marriage">Unión libre / Matrimonio civil</option>
                        <option value="Separated">Separado(a) / Divorciado</option>
                        <option value="Widow">Viudo(a)</option>
                      </select>
                      {fieldErrors.estado_civil && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.estado_civil}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Personas a Cargo <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="personas_a_cargo"
                        min="0"
                        max="15"
                        value={formData.personas_a_cargo === '' ? '' : formData.personas_a_cargo}
                        onChange={handleChange}
                        className={getInputClassName('personas_a_cargo', true)}
                        placeholder="Ej. 1"
                      />
                      {fieldErrors.personas_a_cargo && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.personas_a_cargo}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Tipo de Vivienda <span className="text-rose-500">*</span>
                      </label>
                      <select
                        name="tipo_vivienda"
                        value={formData.tipo_vivienda}
                        onChange={handleChange}
                        className={getSelectClassName('tipo_vivienda')}
                      >
                        <option value="">Seleccione una opción...</option>
                        <option value="House / apartment">Casa / Apartamento propio</option>
                        <option value="Rented apartment">Apartamento en arriendo</option>
                        <option value="With parents">Con padres / familiares</option>
                        <option value="Municipal apartment">Vivienda municipal / social</option>
                        <option value="Office apartment">Oficina / Apartamento comercial</option>
                        <option value="Co-op apartment">Cooperativa de vivienda</option>
                      </select>
                      {fieldErrors.tipo_vivienda && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.tipo_vivienda}</span>
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Step>

              {/* Step 2: Capacidad Financiera y Condiciones del Crédito */}
              <Step title="Capacidad Financiera" description="Flujos y condiciones">
                <div className="space-y-6 animate-in fade-in duration-150 pt-2">
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800/60">
                    <DollarSign className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <span>02. Flujos monetarios, obligaciones y estructura del crédito</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Ingreso Mensual ($) <span className="text-rose-500">*</span>
                      </label>
                      <FormattedCurrencyInput
                        name="ingreso_mensual"
                        value={formData.ingreso_mensual}
                        onChange={handleChange}
                        className={getInputClassName('ingreso_mensual', true)}
                        placeholder="Ej. 1.750.000"
                        required
                      />
                      {fieldErrors.ingreso_mensual && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.ingreso_mensual}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Obligaciones Mensuales ($)
                      </label>
                      <FormattedCurrencyInput
                        name="obligaciones_mensuales"
                        value={formData.obligaciones_mensuales}
                        onChange={handleChange}
                        className={getInputClassName('obligaciones_mensuales', true)}
                        placeholder="Ej. 150.000"
                      />
                      {fieldErrors.obligaciones_mensuales && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.obligaciones_mensuales}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 font-sans">
                          Ingreso Disponible ($) <span className="text-rose-500">*</span>
                        </label>
                        <button
                          type="button"
                          onClick={handleAutoDisposableIncome}
                          className="inline-flex items-center space-x-1 text-[11px] font-mono text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          <Calculator className="w-3 h-3" />
                          <span>Auto-calcular</span>
                        </button>
                      </div>
                      <FormattedCurrencyInput
                        name="ingreso_disponible"
                        value={formData.ingreso_disponible}
                        onChange={handleChange}
                        className={getInputClassName('ingreso_disponible', true)}
                        placeholder="Ej. 1.600.000"
                        required
                      />
                      {fieldErrors.ingreso_disponible && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.ingreso_disponible}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 font-sans">
                          Nivel de Endeudamiento (%) <span className="text-rose-500">*</span>
                        </label>
                        <button
                          type="button"
                          onClick={handleAutoDebtRatio}
                          className="inline-flex items-center space-x-1 text-[11px] font-mono text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          <Calculator className="w-3 h-3" />
                          <span>Auto-calcular</span>
                        </button>
                      </div>
                      <input
                        type="number"
                        name="nivel_endeudamiento_pct"
                        step="0.01"
                        min="0"
                        value={formData.nivel_endeudamiento_pct === '' ? '' : formData.nivel_endeudamiento_pct}
                        onChange={handleChange}
                        className={getInputClassName('nivel_endeudamiento_pct', true)}
                        placeholder="Ej. 93.32"
                      />
                      {fieldErrors.nivel_endeudamiento_pct && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.nivel_endeudamiento_pct}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Monto Solicitado ($) <span className="text-rose-500">*</span>
                      </label>
                      <FormattedCurrencyInput
                        name="monto_solicitado"
                        value={formData.monto_solicitado}
                        onChange={handleChange}
                        className={getInputClassName('monto_solicitado', true)}
                        placeholder="Ej. 25.000.000"
                        required
                      />
                      {fieldErrors.monto_solicitado && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.monto_solicitado}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Plazo del Crédito (meses) <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="plazo_meses"
                        min="1"
                        max="120"
                        value={formData.plazo_meses === '' ? '' : formData.plazo_meses}
                        onChange={handleChange}
                        className={getInputClassName('plazo_meses', true)}
                        placeholder="Ej. 48"
                      />
                      {fieldErrors.plazo_meses && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.plazo_meses}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Tasa de Interés (% E.A.) <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="tasa_interes_ea"
                        step="0.01"
                        min="0"
                        max="120"
                        value={formData.tasa_interes_ea === '' ? '' : formData.tasa_interes_ea}
                        onChange={handleChange}
                        className={getInputClassName('tasa_interes_ea', true)}
                        placeholder="Ej. 49.31"
                      />
                      {fieldErrors.tasa_interes_ea && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.tasa_interes_ea}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 font-sans">
                          Cuota Estimada ($) <span className="text-rose-500">*</span>
                        </label>
                        <button
                          type="button"
                          onClick={handleAutoInstallment}
                          className="inline-flex items-center space-x-1 text-[11px] font-mono text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          <Calculator className="w-3 h-3" />
                          <span>Auto-estimar</span>
                        </button>
                      </div>
                      <FormattedCurrencyInput
                        name="cuota_estimada"
                        value={formData.cuota_estimada}
                        onChange={handleChange}
                        className={getInputClassName('cuota_estimada', true)}
                        placeholder="Ej. 650.000"
                        required
                      />
                      {fieldErrors.cuota_estimada && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.cuota_estimada}</span>
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Step>

              {/* Step 3: Historial Crediticio y Comportamiento de Pago */}
              <Step title="Historial Crediticio" description="Buró y puntualidad">
                <div className="space-y-6 animate-in fade-in duration-150 pt-2">
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800/60">
                    <History className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    <span>03. Centrales de riesgo, morosidad y saldo acumulado</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    {/* Score Buró Hero */}
                    <div className="sm:col-span-2 bg-slate-50/80 dark:bg-slate-900/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700">
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-bold text-slate-900 dark:text-white font-sans">
                          Score Crediticio Oficial (0 - 1000) <span className="text-rose-500">*</span>
                        </label>
                        <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">
                          {formData.score_crediticio !== '' ? `${formData.score_crediticio} pts` : '-'}
                        </span>
                      </div>
                      <input
                        type="number"
                        name="score_crediticio"
                        min="0"
                        max="1000"
                        value={formData.score_crediticio === '' ? '' : formData.score_crediticio}
                        onChange={handleChange}
                        className={getInputClassName('score_crediticio', true, true)}
                        placeholder="Ej. 585"
                      />
                      {fieldErrors.score_crediticio && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.score_crediticio}</span>
                        </p>
                      )}
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
                        Puntaje oficial de comportamiento crediticio. Corresponde a la dimensión con mayor peso relativo en el ensamble neuronal.
                      </p>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Número de Créditos Activos
                      </label>
                      <input
                        type="number"
                        name="numero_creditos_activos"
                        min="0"
                        value={formData.numero_creditos_activos === '' ? '' : formData.numero_creditos_activos}
                        onChange={handleChange}
                        className={getInputClassName('numero_creditos_activos', true)}
                        placeholder="Ej. 2"
                      />
                      {fieldErrors.numero_creditos_activos && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.numero_creditos_activos}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Saldo Total Deuda ($)
                      </label>
                      <FormattedCurrencyInput
                        name="saldo_total_creditos"
                        value={formData.saldo_total_creditos}
                        onChange={handleChange}
                        className={getInputClassName('saldo_total_creditos', true)}
                        placeholder="Ej. 2.500.000"
                      />
                      {fieldErrors.saldo_total_creditos && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.saldo_total_creditos}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Cuotas en Mora Actuales
                      </label>
                      <input
                        type="number"
                        name="numero_cuotas_mora"
                        min="0"
                        value={formData.numero_cuotas_mora === '' ? '' : formData.numero_cuotas_mora}
                        onChange={handleChange}
                        className={getInputClassName('numero_cuotas_mora', true)}
                        placeholder="Ej. 0"
                      />
                      {fieldErrors.numero_cuotas_mora && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.numero_cuotas_mora}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Días Máximos de Mora <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="dias_maximo_mora"
                        min="0"
                        value={formData.dias_maximo_mora === '' ? '' : formData.dias_maximo_mora}
                        onChange={handleChange}
                        className={getInputClassName('dias_maximo_mora', true)}
                        placeholder="Ej. 0"
                      />
                      {fieldErrors.dias_maximo_mora && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.dias_maximo_mora}</span>
                        </p>
                      )}
                    </div>

                    <div className="sm:col-span-2">
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Porcentaje de Pagos Oportunos (% Cumplimiento)
                      </label>
                      <input
                        type="number"
                        name="porcentaje_pagos_oportunos"
                        step="0.1"
                        min="0"
                        max="100"
                        value={formData.porcentaje_pagos_oportunos === '' ? '' : formData.porcentaje_pagos_oportunos}
                        onChange={handleChange}
                        className={getInputClassName('porcentaje_pagos_oportunos', true)}
                        placeholder="Ej. 100.0"
                      />
                      {fieldErrors.porcentaje_pagos_oportunos && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.porcentaje_pagos_oportunos}</span>
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Step>

              {/* Step 4: Perfil Laboral y Relación Institucional */}
              <Step title="Perfil Laboral" description="Ocupación y contrato">
                <div className="space-y-6 animate-in fade-in duration-150 pt-2">
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800/60">
                    <Briefcase className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    <span>04. Relación institucional, estabilidad laboral y patrimonio</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Línea de Negocio <span className="text-rose-500">*</span>
                      </label>
                      <select
                        name="linea_negocio"
                        value={formData.linea_negocio}
                        onChange={handleChange}
                        className={getSelectClassName('linea_negocio')}
                      >
                        <option value="">Seleccione una opción...</option>
                        <option value="Cash loans">Crédito Libre Inversión (Cash loans)</option>
                        <option value="Revolving loans">Crédito Rotativo / Tarjeta (Revolving loans)</option>
                      </select>
                      {fieldErrors.linea_negocio && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.linea_negocio}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Tipo de Contrato / Ocupación <span className="text-rose-500">*</span>
                      </label>
                      <select
                        name="tipo_contrato"
                        value={formData.tipo_contrato}
                        onChange={handleChange}
                        className={getSelectClassName('tipo_contrato')}
                      >
                        <option value="">Seleccione una opción...</option>
                        <option value="Working">Empleado / Asalariado (Working)</option>
                        <option value="Commercial associate">Socio Comercial / Independiente</option>
                        <option value="State servant">Funcionario Público (State servant)</option>
                        <option value="Pensioner">Pensionado / Jubilado (Pensioner)</option>
                        <option value="Businessman">Empresario (Businessman)</option>
                        <option value="Student">Estudiante (Student)</option>
                        <option value="Unemployed">Desempleado (Unemployed)</option>
                        <option value="Otro">Otro Régimen</option>
                      </select>
                      {fieldErrors.tipo_contrato && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.tipo_contrato}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Antigüedad Laboral (años)
                      </label>
                      <input
                        type="number"
                        name="antiguedad_laboral_anios"
                        step="0.1"
                        min="0"
                        max="60"
                        value={formData.antiguedad_laboral_anios === '' ? '' : formData.antiguedad_laboral_anios}
                        onChange={handleChange}
                        className={getInputClassName('antiguedad_laboral_anios', true)}
                        placeholder="Ej. 7.17"
                      />
                      {fieldErrors.antiguedad_laboral_anios && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.antiguedad_laboral_anios}</span>
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Antigüedad como Cliente (años)
                      </label>
                      <input
                        type="number"
                        name="antiguedad_cliente_anios"
                        step="0.1"
                        min="0"
                        max="60"
                        value={formData.antiguedad_cliente_anios === '' ? '' : formData.antiguedad_cliente_anios}
                        onChange={handleChange}
                        className={getInputClassName('antiguedad_cliente_anios', true)}
                        placeholder="Ej. 7.74"
                      />
                      {fieldErrors.antiguedad_cliente_anios && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.antiguedad_cliente_anios}</span>
                        </p>
                      )}
                    </div>

                    <div className="sm:col-span-2">
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5 font-sans">
                        Índice Patrimonial (escala 0 a 10) <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="patrimonio_indice"
                        min="0"
                        max="10"
                        value={formData.patrimonio_indice === '' ? '' : formData.patrimonio_indice}
                        onChange={handleChange}
                        className={getInputClassName('patrimonio_indice', true)}
                        placeholder="Ej. 4"
                      />
                      {fieldErrors.patrimonio_indice && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400 mt-1.5 flex items-center gap-1 font-sans animate-in fade-in duration-150">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                          <span>{fieldErrors.patrimonio_indice}</span>
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Step>

              {/* Step 5: Diagnóstico Pre-Inferencia */}
              <Step title="Diagnóstico Final" description="Revisión y cálculo">
                <div className="space-y-6 animate-in fade-in duration-150 pt-2">
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800/60">
                    <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <span>05. Dossier de validación previo al cálculo de inferencia</span>
                  </div>

                  <div className="bg-slate-50 dark:bg-[#0B1220]/60 rounded-xl p-5 border border-slate-200 dark:border-slate-800 space-y-4 text-xs">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-3.5 gap-x-4">
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Edad / Dependientes</span>
                        <strong className="text-slate-900 dark:text-white font-mono">
                          {formData.edad !== '' ? `${formData.edad} años` : '-'} (
                          {formData.personas_a_cargo !== '' ? `${formData.personas_a_cargo} a cargo` : '-'}
                          )
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Estado Civil</span>
                        <strong className="text-slate-900 dark:text-white">
                          {formData.estado_civil || '-'}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Ingreso Mensual</span>
                        <strong className="text-slate-900 dark:text-white font-mono">
                          {formatCurrencyDisplay(formData.ingreso_mensual)}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Monto Solicitado</span>
                        <strong className="text-slate-900 dark:text-white font-mono">
                          {formatCurrencyDisplay(formData.monto_solicitado)}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Plazo / Cuota</span>
                        <strong className="text-slate-900 dark:text-white font-mono">
                          {formData.plazo_meses !== '' ? `${formData.plazo_meses}m` : '-'} (
                          {formatCurrencyDisplay(formData.cuota_estimada)}
                          )
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Score Buró</span>
                        <strong className="text-blue-600 dark:text-blue-400 font-mono font-bold">
                          {formData.score_crediticio !== '' ? `${formData.score_crediticio} pts` : '-'}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Nivel Endeudamiento</span>
                        <strong className="text-slate-900 dark:text-white font-mono">
                          {formData.nivel_endeudamiento_pct !== '' ? `${formData.nivel_endeudamiento_pct}%` : '-'}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Días Mora Máxima</span>
                        <strong className="text-slate-900 dark:text-white font-mono">
                          {formData.dias_maximo_mora !== '' ? `${formData.dias_maximo_mora} días` : '-'}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block font-sans">Tipo Contrato</span>
                        <strong className="text-slate-900 dark:text-white">
                          {formData.tipo_contrato || '-'}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50/60 dark:bg-blue-950/40 p-4 rounded-xl border border-blue-200/80 dark:border-blue-900/60 text-xs text-blue-950 dark:text-blue-300">
                    <div className="flex items-center space-x-2 font-semibold mb-1">
                      <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
                      <span>Motor de Evaluación: Ensemble Top-3 Diverso (Equiponderado)</span>
                    </div>
                    <p className="text-[11px] text-blue-900/80 dark:text-blue-300/80 leading-relaxed pl-6">
                      El cálculo promediará las salidas probabilísticas de tres redes profundas con semillas y activaciones heterogéneas. Umbral operativo = 50.00%.
                    </p>
                  </div>
                </div>
              </Step>
            </Stepper>

              {/* Bottom Nav Buttons */}
              <div className="mt-8 pt-5 border-t border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between gap-3">
                {currentStep > 1 ? (
                  <button
                    type="button"
                    onClick={handlePrevStep}
                    disabled={isLoading}
                    className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800/60 active:scale-[0.98] transition-colors"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Anterior</span>
                  </button>
                ) : (
                  <div />
                )}

                {currentStep < TOTAL_STEPS ? (
                  <button
                    type="button"
                    onClick={handleNextStep}
                    className="inline-flex items-center space-x-1.5 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm active:scale-[0.98] transition-colors"
                  >
                    <span>Continuar</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleExecuteInference}
                    disabled={isLoading}
                    className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm active:scale-[0.98] disabled:active:scale-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Ejecutando inferencia neuronal...</span>
                      </>
                    ) : (
                      <>
                        <Calculator className="w-3.5 h-3.5" />
                        <span>Ejecutar Predicción</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Printable Report template (visible only on @media print) */}
      {prediction && lastEvaluatedApplicant && (
        <PrintReport
          result={prediction}
          applicant={lastEvaluatedApplicant}
        />
      )}
    </div>
  );
};
