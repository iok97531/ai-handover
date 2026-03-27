import { useState } from 'react'
import { FileText, MessageSquare, ChevronRight, ArrowLeft } from 'lucide-react'

const FORMAT_INSTRUCTION =
  '답변은 문서나 리스트 형식 없이 대화체로 설명해줘. 명령어나 코드만 코드 블록으로 표시하고, 나머지는 자연스럽게 말로 풀어서 얘기해줘.'

interface HandoverFormat {
  id: string
  icon: string
  title: string
  desc: string
  display: string
  instruction: string
}

const HANDOVER_FORMATS: HandoverFormat[] = [
  {
    id: 'overview',
    icon: '🗺️',
    title: '전체 프로젝트 요약',
    desc: '목적·구조·핵심 기능을 빠르게 파악',
    display: '이 프로젝트 전체적으로 인수인계 해줘. 어떤 프로젝트인지, 주요 기능이 뭔지, 구조가 어떻게 생겼는지, 핵심 파일이나 모듈이 어떤 역할을 하는지, 주의할 점은 뭔지 알려줘.',
    instruction: FORMAT_INSTRUCTION
  },
  {
    id: 'onboarding',
    icon: '👨‍💻',
    title: '개발자 온보딩 가이드',
    desc: '기술 스택·아키텍처·코드 구조를 상세히 파악',
    display: '새로 합류한 개발자 입장에서 이 프로젝트 파악하는 데 필요한 걸 인수인계 해줘. 기술 스택, 아키텍처, 데이터 흐름, 디렉토리 구조, 개발 환경 설정 방법, 코딩 규칙 같은 것들.',
    instruction: FORMAT_INSTRUCTION
  },
  {
    id: 'deployment',
    icon: '🚀',
    title: '운영·배포 가이드',
    desc: '배포 방법·환경 설정·인프라 구성 파악',
    display: '이 프로젝트 운영이랑 배포 방법 인수인계 해줘. 빌드·배포 절차, 환경변수 설정, 외부 서비스 의존성, 로그 확인 방법, 장애 대응 방법 포함해서.',
    instruction: FORMAT_INSTRUCTION
  },
  {
    id: 'issues',
    icon: '🔍',
    title: '이슈·기술 부채 현황',
    desc: '알려진 버그·TODO·개선 필요 사항 파악',
    display: '이 프로젝트에서 알아둬야 할 이슈나 기술 부채 인수인계 해줘. TODO/FIXME, 알려진 버그, 리팩토링 필요한 부분, 성능 이슈, 테스트 부족한 부분 포함해서.',
    instruction: FORMAT_INSTRUCTION
  }
]

interface Props {
  onHandover: (display: string, instruction: string) => void
  onDirectQuestion: () => void
}

export default function HandoverWelcome({ onHandover, onDirectQuestion }: Props) {
  const [step, setStep] = useState<'choose' | 'format'>('choose')

  if (step === 'choose') {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-6 px-8">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">이 프로젝트로 무엇을 하시겠어요?</p>
          <p className="mt-2 text-sm text-slate-400">인덱싱이 완료됐습니다. 시작 방법을 선택해주세요.</p>
        </div>
        <div className="flex w-full max-w-sm flex-col gap-3">
          <button
            onClick={() => setStep('format')}
            className="flex items-center gap-4 rounded-xl bg-blue-600/20 border border-blue-500/30 px-5 py-4 text-left transition hover:bg-blue-600/30 hover:border-blue-500/60"
          >
            <FileText size={24} className="shrink-0 text-blue-400" />
            <div>
              <p className="font-semibold text-white">인수인계 받기</p>
              <p className="text-xs text-slate-400">AI가 프로젝트를 분석해 인수인계 문서를 생성합니다</p>
            </div>
            <ChevronRight size={16} className="ml-auto shrink-0 text-slate-500" />
          </button>
          <button
            onClick={onDirectQuestion}
            className="flex items-center gap-4 rounded-xl bg-slate-700/50 border border-slate-600/30 px-5 py-4 text-left transition hover:bg-slate-700 hover:border-slate-500/60"
          >
            <MessageSquare size={24} className="shrink-0 text-slate-300" />
            <div>
              <p className="font-semibold text-white">직접 질문하기</p>
              <p className="text-xs text-slate-400">궁금한 내용을 자유롭게 질문합니다</p>
            </div>
            <ChevronRight size={16} className="ml-auto shrink-0 text-slate-500" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 px-8">
      <div className="text-center">
        <p className="text-2xl font-bold text-white">인수인계 형식을 선택해주세요</p>
        <p className="mt-2 text-sm text-slate-400">목적에 맞는 형식으로 문서를 생성해드립니다</p>
      </div>
      <div className="grid w-full max-w-lg grid-cols-2 gap-3">
        {HANDOVER_FORMATS.map((fmt) => (
          <button
            key={fmt.id}
            onClick={() => onHandover(fmt.display, fmt.instruction)}
            className="flex flex-col gap-2 rounded-xl bg-slate-700/50 border border-slate-600/30 px-4 py-4 text-left transition hover:bg-slate-700 hover:border-slate-500/60"
          >
            <span className="text-2xl">{fmt.icon}</span>
            <p className="font-semibold text-white text-sm">{fmt.title}</p>
            <p className="text-xs text-slate-400 leading-relaxed">{fmt.desc}</p>
          </button>
        ))}
      </div>
      <button
        onClick={() => setStep('choose')}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition"
      >
        <ArrowLeft size={12} />
        뒤로
      </button>
    </div>
  )
}
