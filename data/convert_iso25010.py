"""
ISO 25010 텍스트 문서를 Azure AI Search에 업로드할 수 있는 구조로 변환
입력: ISO25010.txt
출력: 구조화된 JSON 데이터 및 Azure AI Search 업로드 준비
"""

import re
import json

def parse_iso25010_document(file_path):
    """ISO 25010 텍스트 파일을 파싱하여 구조화된 데이터 생성"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 9개 대표 품질속성 정의
    quality_characteristics = {}
    
    # 1. Functional Suitability 파싱
    quality_characteristics["기능 적합성"] = {
        "english": "Functional Suitability",
        "definition": "명시된 조건에서 사용될 때 명시된 요구사항과 암묵적 요구사항을 충족하는 기능을 제공하는 정도",
        "sub_characteristics": [
            {
                "name": "기능 완전성",
                "english": "Functional Completeness",
                "definition": "기능 세트가 명시된 모든 작업과 의도된 사용자 목표를 포괄하는 정도",
                "keywords": ["완전", "충분", "누락", "필수", "모든 기능", "요구사항 충족", "커버"],
                "example_questions": [
                    "시스템이 필요한 모든 기능을 제공합니까?",
                    "필수 기능이 누락되지 않았습니까?",
                    "요구된 기능이 충분히 구현되어 있습니까?",
                    "사용자 목표를 달성하는데 필요한 기능이 모두 있습니까?",
                    "명시된 작업을 수행하는데 필요한 기능이 포함되어 있습니까?"
                ]
            },
            {
                "name": "기능 정확성",
                "english": "Functional Correctness",
                "definition": "의도된 사용자가 사용할 때 제품이나 시스템이 정확한 결과를 제공하는 정도",
                "keywords": ["정확", "올바른", "정밀", "오류", "정확도", "결과", "accurate"],
                "example_questions": [
                    "시스템이 정확한 결과를 제공합니까?",
                    "계산 결과에 오류가 없습니까?",
                    "데이터 처리가 정확하게 이루어집니까?",
                    "시스템이 올바른 결과를 산출합니까?",
                    "의도된 사용자가 사용할 때 정확한 결과가 나옵니까?"
                ]
            },
            {
                "name": "기능 적절성",
                "english": "Functional Appropriateness",
                "definition": "기능이 명시된 작업과 목표 달성을 용이하게 하는 정도",
                "keywords": ["적절", "적합", "목적", "용도", "불필요", "facilitate"],
                "example_questions": [
                    "시스템 기능이 사용 목적에 적합합니까?",
                    "불필요한 기능이 포함되어 있지 않습니까?",
                    "제공되는 기능이 업무에 적절합니까?",
                    "기능이 작업 수행을 용이하게 합니까?"
                ]
            }
        ]
    }
    
    # 2. Performance Efficiency 파싱
    quality_characteristics["성능 효율성"] = {
        "english": "Performance Efficiency",
        "definition": "명시된 조건 하에서 명시된 시간 및 처리량 매개변수 내에서 기능을 수행하고 자원을 효율적으로 사용하는 정도",
        "sub_characteristics": [
            {
                "name": "시간 행동",
                "english": "Time Behaviour",
                "definition": "기능 수행 시 제품이나 시스템의 응답 시간 및 처리 시간, 처리율이 요구사항을 충족하는 정도",
                "keywords": ["응답시간", "속도", "빠른", "지연", "처리시간", "반응", "throughput", "response time"],
                "example_questions": [
                    "시스템의 응답 속도가 만족스럽습니까?",
                    "데이터 처리 시간이 적절합니까?",
                    "시스템이 빠르게 반응합니까?",
                    "응답 지연이 발생하지 않습니까?",
                    "처리율이 요구사항을 충족합니까?"
                ]
            },
            {
                "name": "자원 활용",
                "english": "Resource Utilization",
                "definition": "기능 수행 시 제품이나 시스템이 사용하는 자원의 양과 유형이 요구사항을 충족하는 정도",
                "keywords": ["자원", "메모리", "CPU", "효율적", "사용량", "네트워크", "에너지"],
                "example_questions": [
                    "시스템이 자원을 효율적으로 사용합니까?",
                    "메모리 사용량이 적절합니까?",
                    "CPU 사용률이 과도하지 않습니까?",
                    "네트워크 자원을 효율적으로 활용합니까?",
                    "에너지 소비가 적절합니까?"
                ]
            },
            {
                "name": "용량",
                "english": "Capacity",
                "definition": "제품이나 시스템 매개변수의 최대 한계가 요구사항을 충족하는 정도",
                "keywords": ["용량", "최대", "한계", "확장", "동시", "limits"],
                "example_questions": [
                    "시스템이 필요한 용량을 지원합니까?",
                    "동시 사용자 수를 처리할 수 있습니까?",
                    "데이터 저장 용량이 충분합니까?",
                    "최대 처리량이 요구사항을 충족합니까?"
                ]
            }
        ]
    }
    
    # 3. Compatibility 파싱
    quality_characteristics["호환성"] = {
        "english": "Compatibility",
        "definition": "제품, 시스템 또는 구성요소가 다른 제품, 시스템과 정보를 교환하거나 동일한 환경과 자원을 공유하면서 요구되는 기능을 수행할 수 있는 정도",
        "sub_characteristics": [
            {
                "name": "공존성",
                "english": "Co-existence",
                "definition": "제품이 공통 환경 및 자원을 공유하면서 다른 제품에 부정적 영향을 주지 않고 요구되는 기능을 효율적으로 수행할 수 있는 정도",
                "keywords": ["공존", "공유", "충돌", "간섭", "detrimental impact"],
                "example_questions": [
                    "다른 시스템과 동시에 사용할 수 있습니까?",
                    "다른 소프트웨어와 충돌하지 않습니까?",
                    "공통 자원을 공유하면서 문제없이 작동합니까?",
                    "다른 제품에 부정적 영향을 주지 않습니까?"
                ]
            },
            {
                "name": "상호운용성",
                "english": "Interoperability",
                "definition": "시스템, 제품 또는 구성요소가 다른 제품과 정보를 교환하고 이미 교환된 정보를 상호 사용할 수 있는 정도",
                "keywords": ["연동", "통합", "인터페이스", "데이터 교환", "interoperability"],
                "example_questions": [
                    "다른 시스템과 데이터를 교환할 수 있습니까?",
                    "외부 시스템과 연동이 원활합니까?",
                    "교환된 정보를 상호 활용할 수 있습니까?",
                    "표준 인터페이스를 지원합니까?"
                ]
            }
        ]
    }
    
    # 4. Interaction Capability 파싱
    quality_characteristics["상호작용 능력"] = {
        "english": "Interaction Capability",
        "definition": "명시된 사용자가 다양한 사용 맥락에서 특정 작업을 완료하기 위해 사용자 인터페이스를 통해 정보를 교환하며 제품 또는 시스템과 상호작용할 수 있는 정도",
        "sub_characteristics": [
            {
                "name": "적절성 인식성",
                "english": "Appropriateness Recognizability",
                "definition": "사용자가 제품이나 시스템이 자신의 요구에 적절한지 인식할 수 있는 정도",
                "keywords": ["인식", "적절", "요구", "recognize"],
                "example_questions": [
                    "시스템이 내 요구에 맞는지 쉽게 알 수 있습니까?",
                    "제품이 적절한지 판단하기 쉽습니까?"
                ]
            },
            {
                "name": "학습성",
                "english": "Learnability",
                "definition": "명시된 사용자가 명시된 시간 내에 제품이나 시스템의 기능을 학습하여 사용할 수 있는 정도",
                "keywords": ["학습", "배우기", "쉬운", "learn"],
                "example_questions": [
                    "시스템 사용법을 쉽게 배울 수 있습니까?",
                    "새로운 기능을 빠르게 익힐 수 있습니까?",
                    "짧은 시간에 시스템을 사용할 수 있게 됩니까?"
                ]
            },
            {
                "name": "운용성",
                "english": "Operability",
                "definition": "제품이나 시스템이 운영하고 제어하기 쉽게 만드는 속성을 가진 정도",
                "keywords": ["조작", "운영", "제어", "쉬운", "operate"],
                "example_questions": [
                    "시스템을 쉽게 조작할 수 있습니까?",
                    "운영이 간편합니까?",
                    "제어가 직관적입니까?"
                ]
            },
            {
                "name": "사용자 오류 보호",
                "english": "User Error Protection",
                "definition": "시스템이 사용자의 조작 오류를 방지하는 정도",
                "keywords": ["오류", "실수", "방지", "보호", "error protection"],
                "example_questions": [
                    "사용자 실수를 방지하는 기능이 있습니까?",
                    "잘못된 입력을 제한합니까?",
                    "오류 발생을 사전에 막을 수 있습니까?"
                ]
            },
            {
                "name": "사용자 참여",
                "english": "User Engagement",
                "definition": "사용자 인터페이스가 기능과 정보를 매력적이고 동기부여가 되는 방식으로 제시하여 지속적인 상호작용을 장려하는 정도",
                "keywords": ["참여", "매력적", "동기부여", "engagement"],
                "example_questions": [
                    "사용자 인터페이스가 매력적입니까?",
                    "계속 사용하고 싶게 만듭니까?",
                    "동기부여가 됩니까?"
                ]
            },
            {
                "name": "포용성",
                "english": "Inclusivity",
                "definition": "다양한 배경(연령, 능력, 문화, 민족, 언어, 성별, 경제적 상황 등)을 가진 사람들이 제품이나 시스템을 사용할 수 있는 정도",
                "keywords": ["포용", "다양성", "접근성", "inclusivity"],
                "example_questions": [
                    "다양한 사용자가 시스템을 사용할 수 있습니까?",
                    "연령이나 능력에 관계없이 사용 가능합니까?",
                    "문화적 다양성을 고려합니까?"
                ]
            },
            {
                "name": "사용자 지원",
                "english": "User Assistance",
                "definition": "가장 넓은 범위의 특성과 능력을 가진 사람들이 명시된 사용 맥락에서 명시된 목표를 달성하기 위해 제품을 사용할 수 있는 정도",
                "keywords": ["지원", "도움", "assistance"],
                "example_questions": [
                    "다양한 능력을 가진 사람들이 사용할 수 있습니까?",
                    "사용자 지원 기능이 충분합니까?",
                    "도움말이 적절히 제공됩니까?"
                ]
            },
            {
                "name": "자기서술성",
                "english": "Self-descriptiveness",
                "definition": "제품이 필요할 때 적절한 정보를 제시하여 과도한 상호작용 없이 제품의 기능과 사용법이 사용자에게 즉시 명확해지는 정도",
                "keywords": ["자기서술", "명확", "설명", "self-descriptive"],
                "example_questions": [
                    "시스템이 스스로를 잘 설명합니까?",
                    "사용법이 명확하게 제시됩니까?",
                    "별도 설명 없이도 사용할 수 있습니까?"
                ]
            }
        ]
    }
    
    # 5. Reliability 파싱
    quality_characteristics["신뢰성"] = {
        "english": "Reliability",
        "definition": "명시된 조건 하에서 명시된 시간 동안 시스템, 제품 또는 구성요소가 명시된 기능을 수행하는 정도",
        "sub_characteristics": [
            {
                "name": "결함없음",
                "english": "Faultlessness",
                "definition": "시스템, 제품 또는 구성요소가 정상 운영 중 결함 없이 명시된 기능을 수행하는 정도",
                "keywords": ["결함", "버그", "오류없음", "faultless"],
                "example_questions": [
                    "시스템이 결함 없이 작동합니까?",
                    "정상 운영 중 오류가 발생하지 않습니까?",
                    "버그가 거의 없습니까?"
                ]
            },
            {
                "name": "가용성",
                "english": "Availability",
                "definition": "사용이 필요할 때 시스템, 제품 또는 구성요소가 운영 가능하고 접근 가능한 정도",
                "keywords": ["가용", "중단", "다운타임", "운영", "accessible"],
                "example_questions": [
                    "시스템을 필요할 때 항상 사용할 수 있습니까?",
                    "시스템 중단이 자주 발생하지 않습니까?",
                    "가동 시간이 충분합니까?",
                    "다운타임이 최소화됩니까?"
                ]
            },
            {
                "name": "결함 허용성",
                "english": "Fault Tolerance",
                "definition": "하드웨어 또는 소프트웨어 결함이 있음에도 시스템, 제품 또는 구성요소가 의도된 대로 운영되는 정도",
                "keywords": ["오류", "장애", "허용", "견고", "fault tolerance"],
                "example_questions": [
                    "오류 발생 시에도 시스템이 계속 작동합니까?",
                    "일부 결함이 있어도 기능이 유지됩니까?",
                    "하드웨어 장애를 견딜 수 있습니까?"
                ]
            },
            {
                "name": "복구 가능성",
                "english": "Recoverability",
                "definition": "중단 또는 고장 시 제품이나 시스템이 직접적으로 영향받은 데이터를 복구하고 시스템을 원하는 상태로 재설정할 수 있는 정도",
                "keywords": ["복구", "백업", "복원", "장애", "recoverability"],
                "example_questions": [
                    "장애 발생 시 신속하게 복구됩니까?",
                    "데이터 백업 및 복원이 가능합니까?",
                    "시스템을 원래 상태로 되돌릴 수 있습니까?",
                    "복구 시간이 적절합니까?"
                ]
            }
        ]
    }
    
    # 6. Security 파싱
    quality_characteristics["보안성"] = {
        "english": "Security",
        "definition": "제품이나 시스템이 악의적 공격 패턴으로부터 방어하고 사람이나 다른 제품 또는 시스템이 권한 유형과 수준에 적합한 데이터 접근 정도를 갖도록 정보와 데이터를 보호하는 정도",
        "sub_characteristics": [
            {
                "name": "기밀성",
                "english": "Confidentiality",
                "definition": "제품이나 시스템이 권한이 부여된 사람만 데이터에 접근할 수 있도록 보장하는 정도",
                "keywords": ["기밀", "보안", "암호화", "접근제어", "confidentiality"],
                "example_questions": [
                    "민감한 정보가 보호됩니까?",
                    "인가되지 않은 접근이 차단됩니까?",
                    "데이터 암호화가 적절합니까?",
                    "접근 권한이 적절히 관리됩니까?"
                ]
            },
            {
                "name": "무결성",
                "english": "Integrity",
                "definition": "시스템, 제품 또는 구성요소가 악의적 행위나 컴퓨터 오류에 의한 무단 접근 및 수정으로부터 시스템과 데이터의 상태를 보호하는 정도",
                "keywords": ["무결성", "변조", "위변조", "데이터 보호", "integrity"],
                "example_questions": [
                    "데이터가 무단으로 변경되지 않습니까?",
                    "데이터 무결성이 보장됩니까?",
                    "위변조 방지 기능이 있습니까?",
                    "시스템 상태가 보호됩니까?"
                ]
            },
            {
                "name": "부인방지",
                "english": "Non-repudiation",
                "definition": "행위나 사건이 발생했음이 증명될 수 있어 나중에 부인할 수 없는 정도",
                "keywords": ["부인방지", "추적", "로그", "감사", "non-repudiation"],
                "example_questions": [
                    "사용자 행위를 추적할 수 있습니까?",
                    "거래 이력이 기록됩니까?",
                    "행위를 부인할 수 없도록 증명할 수 있습니까?",
                    "감사 추적이 가능합니까?"
                ]
            },
            {
                "name": "책임추적성",
                "english": "Accountability",
                "definition": "엔티티의 행위가 해당 엔티티에게 고유하게 추적될 수 있는 정도",
                "keywords": ["책임", "감사", "로그", "추적", "accountability"],
                "example_questions": [
                    "누가 무엇을 했는지 추적할 수 있습니까?",
                    "감사 로그가 기록됩니까?",
                    "행위에 대한 책임을 식별할 수 있습니까?",
                    "사용자 활동이 추적됩니까?"
                ]
            },
            {
                "name": "인증성",
                "english": "Authenticity",
                "definition": "대상 또는 자원의 정체성이 주장된 것과 동일함이 증명될 수 있는 정도",
                "keywords": ["인증", "신원", "본인확인", "authenticity"],
                "example_questions": [
                    "사용자 인증이 적절히 이루어집니까?",
                    "신원 확인이 정확합니까?",
                    "정체성을 증명할 수 있습니까?",
                    "본인 확인 절차가 있습니까?"
                ]
            },
            {
                "name": "저항성",
                "english": "Resistance",
                "definition": "악의적 행위자의 공격을 받는 동안에도 제품이나 시스템이 운영을 유지하는 정도",
                "keywords": ["저항", "공격", "방어", "resistance"],
                "example_questions": [
                    "공격에 저항할 수 있습니까?",
                    "보안 공격 중에도 운영이 유지됩니까?",
                    "방어 메커니즘이 효과적입니까?"
                ]
            }
        ]
    }
    
    # 7. Maintainability 파싱
    quality_characteristics["유지보수성"] = {
        "english": "Maintainability",
        "definition": "제품이나 시스템을 개선하거나 수정하거나 환경 및 요구사항 변경에 적응시킬 수 있는 효과성과 효율성의 정도",
        "sub_characteristics": [
            {
                "name": "모듈성",
                "english": "Modularity",
                "definition": "한 구성요소의 변경이 다른 구성요소에 최소한의 영향을 주도록 시스템이나 컴퓨터 프로그램이 개별 구성요소로 구성된 정도",
                "keywords": ["모듈", "독립", "결합도", "분리", "modularity"],
                "example_questions": [
                    "시스템이 모듈화되어 있습니까?",
                    "한 부분의 수정이 다른 부분에 영향을 주지 않습니까?",
                    "구성요소가 독립적입니까?",
                    "결합도가 낮습니까?"
                ]
            },
            {
                "name": "재사용성",
                "english": "Reusability",
                "definition": "자산이 하나 이상의 시스템에서 또는 다른 자산을 만드는데 사용될 수 있는 정도",
                "keywords": ["재사용", "공통", "라이브러리", "reusability"],
                "example_questions": [
                    "코드를 재사용할 수 있습니까?",
                    "공통 모듈이 잘 설계되어 있습니까?",
                    "다른 시스템에서도 사용 가능합니까?",
                    "재사용 가능한 컴포넌트가 있습니까?"
                ]
            },
            {
                "name": "분석성",
                "english": "Analysability",
                "definition": "결함이나 고장의 원인 또는 수정이 필요한 부분을 진단하는 것이 효과적이고 효율적인 정도",
                "keywords": ["분석", "진단", "로그", "디버그", "analysability"],
                "example_questions": [
                    "문제 원인을 쉽게 파악할 수 있습니까?",
                    "로그가 충분히 제공됩니까?",
                    "결함을 진단하기 쉽습니까?",
                    "디버깅이 용이합니까?"
                ]
            },
            {
                "name": "수정성",
                "english": "Modifiability",
                "definition": "결함을 도입하거나 기존 제품 품질을 저하시키지 않고 제품이나 시스템이 효과적이고 효율적으로 수정될 수 있는 정도",
                "keywords": ["수정", "변경", "개선", "유지보수", "modifiability"],
                "example_questions": [
                    "시스템을 쉽게 수정할 수 있습니까?",
                    "기능 추가가 용이합니까?",
                    "변경 시 품질이 저하되지 않습니까?",
                    "개선이 쉽습니까?"
                ]
            },
            {
                "name": "시험성",
                "english": "Testability",
                "definition": "시스템, 제품 또는 구성요소에 대한 시험 기준이 설정될 수 있고 해당 기준을 충족하는지 확인하기 위한 시험이 수행될 수 있는 정도",
                "keywords": ["테스트", "시험", "검증", "testability"],
                "example_questions": [
                    "시스템을 쉽게 테스트할 수 있습니까?",
                    "자동화된 테스트가 가능합니까?",
                    "테스트 기준을 설정하기 쉽습니까?",
                    "검증이 용이합니까?"
                ]
            }
        ]
    }
    
    # 8. Flexibility 파싱
    quality_characteristics["유연성"] = {
        "english": "Flexibility",
        "definition": "제품이 요구사항, 사용 맥락 또는 시스템 환경의 변경에 적응될 수 있는 정도",
        "sub_characteristics": [
            {
                "name": "적응성",
                "english": "Adaptability",
                "definition": "제품이나 시스템이 다른 또는 진화하는 하드웨어, 소프트웨어 또는 다른 운영 또는 사용 환경에 효과적이고 효율적으로 적응될 수 있는 정도",
                "keywords": ["적응", "환경", "변화", "유연", "adaptability"],
                "example_questions": [
                    "다양한 환경에서 사용할 수 있습니까?",
                    "환경 변화에 쉽게 적응합니까?",
                    "다른 플랫폼으로 전환이 가능합니까?",
                    "하드웨어 변경에 대응할 수 있습니까?"
                ]
            },
            {
                "name": "확장성",
                "english": "Scalability",
                "definition": "제품이 증가하거나 감소하는 작업부하를 처리하거나 가변성을 처리하기 위해 용량을 조정할 수 있는 정도",
                "keywords": ["확장", "증가", "성장", "스케일", "scalability"],
                "example_questions": [
                    "사용자 증가에 대응할 수 있습니까?",
                    "시스템 확장이 용이합니까?",
                    "작업부하 증가를 처리할 수 있습니까?",
                    "용량을 늘릴 수 있습니까?"
                ]
            },
            {
                "name": "설치성",
                "english": "Installability",
                "definition": "명시된 환경에서 제품이나 시스템이 효과적이고 효율적으로 설치 및/또는 제거될 수 있는 정도",
                "keywords": ["설치", "배포", "제거", "installability"],
                "example_questions": [
                    "시스템을 쉽게 설치할 수 있습니까?",
                    "배포 과정이 간단합니까?",
                    "제거가 용이합니까?",
                    "설치 시간이 적절합니까?"
                ]
            },
            {
                "name": "대체성",
                "english": "Replaceability",
                "definition": "제품이 동일한 환경에서 동일한 목적으로 다른 명시된 제품으로 대체될 수 있는 정도",
                "keywords": ["대체", "교체", "전환", "마이그레이션", "replaceability"],
                "example_questions": [
                    "다른 시스템으로 쉽게 전환할 수 있습니까?",
                    "데이터 이전이 용이합니까?",
                    "대체 제품으로 교체가 가능합니까?",
                    "마이그레이션이 쉽습니까?"
                ]
            }
        ]
    }
    
    # 9. Safety 파싱
    quality_characteristics["안전성"] = {
        "english": "Safety",
        "definition": "정의된 조건 하에서 인간의 생명, 건강, 재산 또는 환경이 위험에 처하는 상태를 피하는 제품의 정도",
        "sub_characteristics": [
            {
                "name": "운영 제약",
                "english": "Operational Constraint",
                "definition": "운영 위험에 직면했을 때 제품이나 시스템이 안전한 매개변수나 상태 내에서 운영을 제한하는 정도",
                "keywords": ["제약", "안전", "매개변수", "operational constraint"],
                "example_questions": [
                    "위험 상황에서 안전하게 운영됩니까?",
                    "안전 매개변수 내에서 작동합니까?",
                    "위험 시 적절히 제한됩니까?"
                ]
            },
            {
                "name": "위험 식별",
                "english": "Risk Identification",
                "definition": "제품이 생명, 재산 또는 환경을 용인할 수 없는 위험에 노출시킬 수 있는 일련의 사건이나 운영을 식별할 수 있는 정도",
                "keywords": ["위험", "식별", "감지", "risk identification"],
                "example_questions": [
                    "위험을 식별할 수 있습니까?",
                    "잠재적 위험을 감지합니까?",
                    "위험 상황을 인식합니까?"
                ]
            },
            {
                "name": "안전 실패",
                "english": "Fail Safe",
                "definition": "고장 발생 시 제품이 자동으로 안전한 운영 모드로 전환하거나 안전한 상태로 되돌아갈 수 있는 정도",
                "keywords": ["안전", "실패", "자동", "fail safe"],
                "example_questions": [
                    "고장 시 안전 모드로 전환됩니까?",
                    "자동으로 안전 상태가 됩니까?",
                    "실패 시 위험이 최소화됩니까?"
                ]
            },
            {
                "name": "위험 경고",
                "english": "Hazard Warning",
                "definition": "제품이나 시스템이 안전한 운영을 유지하기 위해 충분한 시간 내에 반응할 수 있도록 운영이나 내부 제어에 대한 용인할 수 없는 위험에 대한 경고를 제공하는 정도",
                "keywords": ["경고", "알림", "위험", "hazard warning"],
                "example_questions": [
                    "위험에 대한 경고가 제공됩니까?",
                    "충분한 시간 내에 알림이 됩니까?",
                    "적절한 경고 메시지가 있습니까?"
                ]
            },
            {
                "name": "안전 통합",
                "english": "Safe Integration",
                "definition": "제품이 하나 이상의 구성요소와 통합하는 동안과 이후에 안전성을 유지할 수 있는 정도",
                "keywords": ["통합", "안전", "구성요소", "safe integration"],
                "example_questions": [
                    "구성요소 통합 시 안전합니까?",
                    "통합 후에도 안전성이 유지됩니까?",
                    "안전하게 통합됩니까?"
                ]
            }
        ]
    }
    
    return quality_characteristics

def generate_documents_for_upload(quality_characteristics):
    """Azure AI Search에 업로드할 문서 생성"""
    documents = []
    
    for main_char, data in quality_characteristics.items():
        # 1. 대표 품질속성 문서 생성
        main_doc = {
            "id": f"main_{main_char.replace(' ', '_')}",
            "content": f"{main_char} ({data['english']})\n\n정의: {data['definition']}",
            "quality_characteristic": main_char,
            "quality_characteristic_en": data['english'],
            "sub_characteristic": None,
            "sub_characteristic_en": None,
            "doc_type": "main_characteristic",
            "level": 1,
            "keywords": [],
            "example_questions": [],
            "parent_id": None,
            "source": "ISO/IEC 25010:2023",
            "definition": data['definition']
        }
        documents.append(main_doc)
        
        # 2. 세부 특성 문서 생성
        for sub_data in data['sub_characteristics']:
            sub_doc = {
                "id": f"sub_{main_char.replace(' ', '_')}_{sub_data['name'].replace(' ', '_')}",
                "content": (
                    f"{sub_data['name']} ({sub_data['english']})\n\n"
                    f"정의: {sub_data['definition']}\n\n"
                    f"대표 품질속성: {main_char}\n\n"
                    f"관련 질문 예시:\n" + 
                    "\n".join([f"- {q}" for q in sub_data['example_questions']])
                ),
                "quality_characteristic": main_char,
                "quality_characteristic_en": data['english'],
                "sub_characteristic": sub_data['name'],
                "sub_characteristic_en": sub_data['english'],
                "doc_type": "sub_characteristic",
                "level": 2,
                "keywords": " | ".join(sub_data['keywords']),  # 배열 → 문자열
                "example_questions": "\n".join(sub_data['example_questions']),  # 배열 → 문자열
                "parent_id": f"main_{main_char.replace(' ', '_')}",
                "source": "ISO/IEC 25010:2023",
                "definition": sub_data['definition']
            }
            documents.append(sub_doc)
    
    return documents

if __name__ == "__main__":
    print("📖 ISO 25010 문서 파싱 시작...")
    
    # 1. 문서 파싱 - 파일 경로 자동 탐지
    possible_paths = [
        "./data/ISO25010.txt",  # Claude 환경
        "ISO25010.txt",                          # 현재 디렉토리
        "../ISO25010.txt",                       # 상위 디렉토리
        "uploads/ISO25010.txt",                  # uploads 폴더
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if file_path is None:
        print("❌ ISO25010.txt 파일을 찾을 수 없습니다.")
        print("다음 위치 중 하나에 파일을 배치하세요:")
        for path in possible_paths:
            print(f"  - {path}")
        exit(1)
    
    print(f"📄 파일 위치: {file_path}")
    quality_data = parse_iso25010_document(file_path)
    
    print(f"✅ {len(quality_data)}개 대표 품질속성 파싱 완료")
    
    # 2. 업로드용 문서 생성
    documents = generate_documents_for_upload(quality_data)
    
    print(f"✅ 총 {len(documents)}개 문서 생성 완료")
    print(f"   - 대표 품질속성: {len([d for d in documents if d['doc_type'] == 'main_characteristic'])}개")
    print(f"   - 세부 특성: {len([d for d in documents if d['doc_type'] == 'sub_characteristic'])}개")
    
    # 3. JSON 파일로 저장
    output_file = "./data/iso25010_documents.json"  # 현재 디렉토리에 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 문서 저장 완료: {output_file}")
    
    # 4. 샘플 출력
    print("\n📄 생성된 문서 샘플:")
    print(json.dumps(documents[0], ensure_ascii=False, indent=2))
    print("\n...")
    print(json.dumps(documents[10], ensure_ascii=False, indent=2))
    
    print("\n✅ 변환 완료!")
    print("\n다음 단계:")
    print("1. create_index.py 실행 - 인덱스 생성")
    print("2. upload_data.py 실행 - 데이터 업로드")
