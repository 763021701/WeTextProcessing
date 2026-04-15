# Copyright (c) 2022 Xingchen Song (sxc19@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pynini import accep, cross, string_file, union
from pynini.lib.pynutil import add_weight, delete, insert

from itn.chinese.rules.cardinal import Cardinal
from tn.processor import Processor
from tn.utils import get_abs_path


class Measure(Processor):

    def __init__(self, exclude_one=True, enable_0_to_9=True):
        super().__init__(name="measure")
        self.exclude_one = exclude_one
        self.enable_0_to_9 = enable_0_to_9
        self.build_tagger()
        self.build_verbalizer()

    def build_tagger(self):
        units_en = string_file(get_abs_path("../itn/chinese/data/measure/units_en.tsv"))
        units_zh = string_file(get_abs_path("../itn/chinese/data/measure/units_zh.tsv"))
        sign = string_file(get_abs_path("../itn/chinese/data/number/sign.tsv"))  # + -
        digit = string_file(get_abs_path("../itn/chinese/data/number/digit.tsv"))  # 1 ~ 9
        digit_zh = string_file(get_abs_path("../itn/chinese/data/number/digit_zh.tsv"))  # 1 ~ 9
        addzero = insert("0")
        to = union(cross("到", "~"), cross("至", "~"), cross("到百分之", "~"), cross("至百分之", "~"))

        units = add_weight((accep("亿") | accep("兆") | accep("万")), -0.5).ques + units_zh
        units |= add_weight((cross("亿", "00M") | cross("兆", "T") | cross("万", "W")), -0.5).ques + (
            add_weight(units_en, -1.0)
        )

        number = Cardinal().number if self.enable_0_to_9 else Cardinal().number_exclude_0_to_9
        ascii_int = union(*[cross(str(d), str(d)) for d in "0123456789"]).plus.optimize()
        ascii_dec = ascii_int + cross(".", ".") + ascii_int.plus
        num_or_ascii = number | ascii_int | ascii_dec
        num_scaled = number | ascii_int | ascii_dec

        # SI 浓度/活力：分子 [摩尔|克|单位|国际单位|细胞系|RU/TU|升系] 每 分母 [升|克]（升/升、毫升/升等）
        def _si_cross(*pairs):
            return union(*[cross(a, b) for a, b in pairs]).optimize()

        si_num_mol = _si_cross(
            ("飞摩尔", "fmol"),
            ("皮摩尔", "pmol"),
            ("纳摩尔", "nmol"),
            ("微摩尔", "μmol"),
            ("毫摩尔", "mmol"),
            ("千摩尔", "kmol"),
            ("摩尔", "mol"),
        )
        si_num_g = _si_cross(
            ("飞克", "fg"),
            ("皮克", "pg"),
            ("纳克", "ng"),
            ("微克", "μg"),
            ("毫克", "mg"),
            ("千克", "kg"),
            ("公斤", "kg"),
            ("克", "g"),
        )
        si_num_u = _si_cross(
            ("飞单位", "fU"),
            ("皮单位", "pU"),
            ("纳单位", "nU"),
            ("微单位", "μU"),
            ("毫单位", "mU"),
            ("千单位", "KU"),
            ("单位", "U"),
        )
        si_num_iu = _si_cross(
            ("飞国际单位", "fIU"),
            ("皮国际单位", "pIU"),
            ("纳国际单位", "nIU"),
            ("微国际单位", "μIU"),
            ("毫国际单位", "mIU"),
            ("千国际单位", "KIU"),
            ("国际单位", "IU"),
        )
        # 相对/治疗单位（与通用「毫单位」等区分，整词匹配）
        si_num_special_u = _si_cross(
            ("相对单位", "RU"),
            ("治疗单位", "TU"),
        )
        si_num_named_u = _si_cross(
            ("菌落形成单位", "CFU"),
            ("噬斑形成单位", "PFU"),
            ("贝塞斯达单位", "BU"),
            ("内毒素单位", "EU"),
            ("血小板当量国际单位", "PEIU"),
            ("PEI单位", "PEIU"),
            ("PE国际单位", "PEIU"),
            ("毫吸光度单位", "mAU"),
            ("毫吸收单位", "mAU"),
            ("毫当量", "mEq"),
            ("微当量", "μEq"),
            ("当量", "Eq"),
        )
        si_num_cells = _si_cross(
            ("白细胞", "WBC"),
            ("红细胞", "RBC"),
            ("细胞", "cells"),
            ("拷贝", "copies"),
        )
        si_vol = _si_cross(
            ("飞升", "fL"),
            ("皮升", "pL"),
            ("纳升", "nL"),
            ("微升", "μL"),
            ("毫升", "mL"),
            ("分升", "dL"),
            ("千升", "kL"),
            ("升", "L"),
        )
        si_num = (
            si_num_mol
            | si_num_g
            | si_num_u
            | si_num_iu
            | si_num_special_u
            | si_num_named_u
            | si_num_cells
            | si_vol
        )
        si_den_vol = si_vol
        si_den_g = _si_cross(
            ("飞克", "fg"),
            ("皮克", "pg"),
            ("纳克", "ng"),
            ("微克", "μg"),
            ("毫克", "mg"),
            ("千克", "kg"),
            ("公斤", "kg"),
            ("克", "g"),
        )
        si_den = si_den_vol | si_den_g
        si_density_body = si_num + delete("每") + insert("/") + si_den
        measure_si_density = add_weight(si_density_body, -0.52)
        osm_num = _si_cross(
            ("毫渗量", "mOsm"),
            ("毫渗摩尔", "mOsm"),
            ("渗量", "Osm"),
            ("渗摩尔", "Osm"),
            ("渗透压摩尔", "Osm"),
        )
        osm_den = _si_cross(
            ("公斤水", "kgH₂O"),
            ("千克水", "kgH₂O"),
            ("公斤", "kg"),
            ("千克", "kg"),
            ("升", "L"),
        )
        measure_osm = add_weight(osm_num + delete("每") + insert("/") + osm_den, -0.52)
        # 数量 + SI 浓度/活力；可选量词「个」（如「十个细胞每微升」→10cells/μL；「五点六毫摩尔每升」无「个」）
        measure_num_si_density = add_weight(
            num_or_ascii + delete("个").ques + si_density_body,
            -0.55,
        )
        # 口语「N个每微升」等，与 units_en 中 /μL、/LPF 写法一致
        count_per_den = _si_cross(
            ("每微升", "/μL"),
            ("每低倍视野", "/LPF"),
            ("每高倍视野", "/HPF"),
        )
        measure_num_count_per = add_weight(num_or_ascii + delete("个") + count_per_den, -0.55)

        wbc_rbc_abbr = cross("白细胞", "WBC") | cross("红细胞", "RBC")
        wbc_rbc_braced = cross("白细胞", "{WBC}") | cross("红细胞", "{RBC}")
        cell_copy_braced = cross("细胞", "{cells}") | cross("拷贝", "{copies}")
        platelet_braced = cross("血小板", "{platelets}")
        wbc_rbc_cell_copy_braced = wbc_rbc_braced | cell_copy_braced | platelet_braced
        # 每 + 数 + 白/红细胞（如「每一百白细胞」→/100WBC）；权重优于 number+units 拆开
        measure_per_count_wbc_rbc = add_weight(
            delete("每") + insert("/") + num_or_ascii + wbc_rbc_abbr,
            -0.57,
        )

        # 每克/每摩尔肌酐（Cr）：分子为摩尔|克|单位|IU|细胞|RU/TU（不含升作分子，避免误配）
        si_den_mol = si_num_mol
        si_num_cr = (
            si_num_mol | si_num_g | si_num_u | si_num_iu | si_num_special_u | si_num_cells
        )
        measure_si_creatinine = add_weight(
            si_num_cr
            + delete("每")
            + insert("/")
            + (si_den_g | si_den_mol)
            + delete("肌酐")
            + insert(" Cr"),
            -0.56,
        )

        # 血流动力学等：体积流量/时间/压力，如「立方厘米每分钟每毫米汞柱」→ cm³/min/mmHg
        vol_flow_num = _si_cross(
            ("立方厘米", "cm³"),
            ("立方分米", "dm³"),
            ("立方米", "m³"),
            ("毫升", "mL"),
            ("微升", "μL"),
            ("升", "L"),
        )
        time_mid = _si_cross(
            ("分钟", "min"),
            ("小时", "h"),
            ("秒", "s"),
        )
        time_triple = time_mid | _si_cross(
            ("二十四小时", "24h"),
            ("24小时", "24h"),
            ("48小时", "48h"),
            ("四十八小时", "48h"),
            ("72小时", "72h"),
            ("七十二小时", "72h"),
            ("每天", "d"),
        )
        time_triple_tail = (time_triple | cross("天", "d")).optimize()
        # 仅「每二十四小时」等剂量时段，不含分/时/秒（避免与「二毫升每分钟每…㎡」三连抢前缀）
        time_dose_only = _si_cross(
            ("二十四小时", "24h"),
            ("24小时", "24h"),
            ("48小时", "48h"),
            ("四十八小时", "48h"),
            ("72小时", "72h"),
            ("七十二小时", "72h"),
            ("每天", "d"),
        )
        time_arabic_h = _si_cross(*[(f"{n}小时", f"{n}h") for n in range(1, 25)])
        time_zh_n_hour = _si_cross(
            ("一小时", "1h"),
            ("二小时", "2h"),
            ("两小时", "2h"),
            ("三小时", "3h"),
            ("四小时", "4h"),
            ("五小时", "5h"),
            ("六小时", "6h"),
            ("七小时", "7h"),
            ("八小时", "8h"),
            ("九小时", "9h"),
            ("十小时", "10h"),
            ("十一小时", "11h"),
            ("十二小时", "12h"),
            ("十三小时", "13h"),
            ("十四小时", "14h"),
            ("十五小时", "15h"),
            ("十六小时", "16h"),
            ("十七小时", "17h"),
            ("十八小时", "18h"),
            ("十九小时", "19h"),
            ("二十小时", "20h"),
            ("二十一小时", "21h"),
            ("二十二小时", "22h"),
            ("二十三小时", "23h"),
        )
        # 单字「小时」→ h（如「十克每小时」）；不含「分钟」以免与「…毫升每分钟每…」三连抢前缀
        time_num_rate = (time_dose_only | time_arabic_h | time_zh_n_hour | cross("小时", "h")).optimize()
        time_plain_rate = (
            time_num_rate
            | (number + delete("分钟") + insert("min"))
            | cross("分钟", "min")
            | (number + delete("秒") + insert("s"))
            | cross("秒", "s")
        ).optimize()
        # 数量 + SI 量词 + 每 + 剂量/数字小时（如「十克每二十四小时」→10g/24h，「十克每8小时」→10g/8h）
        measure_num_per_time = add_weight(
            number + si_num + delete("每") + insert("/") + time_num_rate,
            -0.54,
        )
        measure_si_per_time = add_weight(
            si_num + delete("每") + insert("/") + time_plain_rate,
            -0.55,
        )
        measure_per_time = add_weight(delete("每") + insert("/") + time_plain_rate, -0.55)
        measure_num_count_per_time = add_weight(
            num_or_ascii + delete("次") + delete("每") + insert("/") + time_plain_rate,
            -2.0,
        )
        measure_per_time_num_count = add_weight(
            delete("每")
            + (
                (delete("秒") + num_or_ascii + delete("次") + insert("/s"))
                | (delete("分钟") + num_or_ascii + delete("次") + insert("/min"))
                | (delete("小时") + num_or_ascii + delete("次") + insert("/h"))
            ),
            -2.0,
        )
        energy_units = _si_cross(
            ("千卡", "kcal"),
            ("千焦", "kJ"),
        )
        measure_energy_per_time = add_weight(
            energy_units + delete("每") + insert("/") + time_num_rate,
            -0.55,
        )
        pressure_tail = _si_cross(
            ("毫米汞柱", "mmHg"),
            ("厘米水柱", "cmH₂O"),
        )
        area_m2 = cross("平方米", "m²")
        area_cm2 = cross("平方厘米", "cm²")
        # 任意「数词 + 平方米」→ Nm²（如 1.73、二点五），用于 mL/min/Nm² 等
        area_scaled_m2 = num_scaled + delete("平方米") + insert("m²")
        # 三连（两「每」）：多语序模板并集，权重优于 number+units_en 短匹配
        si_num_triple = si_num_mol | si_num_g | si_num_u | si_num_iu
        # 临床「每 10^n 个红细胞」分母（不含体积作分子，避免 mL/10^6{RBC}）
        si_num_for_scaled_denom = si_num_mol | si_num_g | si_num_u | si_num_iu
        triple_vol_time_pressure = (
            vol_flow_num
            + delete("每")
            + insert("/")
            + time_mid
            + delete("每")
            + insert("/")
            + pressure_tail
        )
        triple_vol_time_area_scaled = (
            vol_flow_num + delete("每") + insert("/") + time_mid + delete("每") + insert("/") + area_scaled_m2
        )
        triple_vol_time_m2 = (
            vol_flow_num + delete("每") + insert("/") + time_mid + delete("每") + insert("/") + area_m2
        )
        triple_si_time_g = (
            si_num_triple + delete("每") + insert("/") + time_triple + delete("每") + insert("/") + si_den_g
        )
        triple_si_g_time = (
            si_num_triple + delete("每") + insert("/") + si_den_g + delete("每") + insert("/") + time_triple_tail
        )
        triple_si_time_vol = (
            si_num_triple + delete("每") + insert("/") + time_triple + delete("每") + insert("/") + si_den_vol
        )
        triple_time_si_vol = (
            time_mid + delete("每") + insert("/") + si_num_triple + delete("每") + insert("/") + si_den_vol
        )
        triple_si_vol_time = (
            si_num_triple + delete("每") + insert("/") + si_den_vol + delete("每") + insert("/") + time_mid
        )
        triple_vol_g_time = (
            vol_flow_num + delete("每") + insert("/") + si_den_g + delete("每") + insert("/") + time_mid
        )
        triple_vol_time_g = (
            vol_flow_num + delete("每") + insert("/") + time_mid + delete("每") + insert("/") + si_den_g
        )
        triple_si_m2_time = (
            si_num_triple + delete("每") + insert("/") + area_m2 + delete("每") + insert("/") + time_mid
        )
        triple_cmh2o_l_s = (
            cross("厘米水柱", "cmH₂O")
            + delete("每")
            + insert("/")
            + cross("升", "L")
            + delete("每")
            + insert("/")
            + cross("秒", "s")
        )
        # 秒|分|时 + 每 + 平方厘米 + 每 + 平方米（如「十秒每平方厘米每平方米」→10s/cm²/m²）
        triple_time_cm2_m2 = (
            time_mid
            + delete("每")
            + insert("/")
            + area_cm2
            + delete("每")
            + insert("/")
            + area_m2
        )
        triple_suffix_core = (
            triple_vol_time_pressure
            | triple_vol_time_area_scaled
            | triple_vol_time_m2
            | triple_si_time_g
            | triple_si_g_time
            | triple_si_time_vol
            | triple_time_si_vol
            | triple_si_vol_time
            | triple_vol_g_time
            | triple_vol_time_g
            | triple_si_m2_time
            | triple_cmh2o_l_s
            | triple_time_cm2_m2
        ).optimize()
        measure_num_per_m2 = add_weight(
            number + (si_num_triple | vol_flow_num) + delete("每") + insert("/") + area_m2,
            -0.54,
        )
        measure_triple_plain = add_weight(triple_suffix_core, -1.07)

        # 科学计数 +（units_en 特例 | SI 组合），因摩尔/克等浓度已迁出 TSV
        exp_one = digit
        exp_teen = cross("十", "1") + (digit | add_weight(addzero, 0.1))
        exp_tens = digit + delete("十") + (digit | add_weight(addzero, 0.1))
        sci_exp = exp_one | exp_teen | exp_tens
        sci_exp_signed = (delete("负") + insert("-")).ques + sci_exp
        sci_plain_core = delete("十") + delete("的") + insert("10^") + sci_exp_signed + delete("次方")
        sci_times_core = delete("十") + delete("的") + insert("×10^") + sci_exp_signed + delete("次方")
        # 「乘」与「乘以」均视为 ×10^…（口语常省略「以」）
        sci_body = sci_plain_core | (delete("乘") + delete("以").ques + sci_times_core)
        # 「八乘十的八次方」→8x10^8（系数在乘号前，与 ×10^ 口语分支区分）
        zh_coef_one_digit = union(
            *[cross(a, b) for a, b in zip("一二三四五六七八九", "123456789")]
        )
        sci_coef_times_tail = (
            delete("十") + delete("的") + insert("10^") + sci_exp_signed + delete("次方")
        )
        sci_coef_body = (
            zh_coef_one_digit + insert("x") + delete("乘") + delete("以").ques + sci_coef_times_tail
        )
        sci_body_scaled = (sci_coef_body | sci_body).optimize()
        scaled_den_cells_bundle = delete("一").ques + sci_body_scaled + wbc_rbc_cell_copy_braced
        triple_si_time_scaled_cells = (
            si_num_triple
            + delete("每")
            + insert("/")
            + time_mid
            + delete("每")
            + insert("/")
            + scaled_den_cells_bundle
        )
        triple_suffix = (triple_suffix_core | triple_si_time_scaled_cells).optimize()
        measure_triple = add_weight(number + triple_suffix, -2.2)
        per_scaled_wbc_rbc_suffix = (
            delete("每") + insert("/") + scaled_den_cells_bundle
        )
        measure_per_scaled_wbc_rbc = add_weight(per_scaled_wbc_rbc_suffix, -0.57)
        measure_si_per_scaled_wbc_rbc = add_weight(
            si_num_for_scaled_denom
            + delete("每")
            + insert("/")
            + scaled_den_cells_bundle,
            -0.58,
        )
        latin_token = (self.ALPHA | self.DIGIT).plus
        latin_label = (latin_token + (accep(" ") + latin_token).plus).optimize()
        measure_latin_prefix_u_per_vol = add_weight(
            (
                latin_label
                + insert(" ")
                + (cross("国际单位", "U") | cross("单位", "U"))
                + delete("每")
                + insert("/")
                + si_den_vol
            )
            | (
                latin_token
                + cross("单位", "U")
                + delete("每")
                + insert("/")
                + si_den_vol
            )
            | (latin_token + delete("每") + insert("/") + si_den_vol),
            -0.57,
        )
        lab_acronym_per_vol = union("CCU") + delete("每") + insert("/") + si_den_vol
        measure_lab_acronym_per_vol = add_weight(lab_acronym_per_vol, -0.57)
        measure_num_lab_acronym_per_vol = add_weight(num_or_ascii + lab_acronym_per_vol, -0.57)
        measure_sci_lab_acronym_per_vol = add_weight(delete("一").ques + sci_body_scaled + lab_acronym_per_vol, -0.58)
        sci_denom_plain = delete("一").ques + sci_plain_core
        sci_denom_coef = (
            num_or_ascii
            + delete("乘")
            + delete("以").ques
            + delete("十")
            + delete("的")
            + insert("×10^")
            + sci_exp_signed
            + delete("次方")
        )
        sci_scaled_denom = (sci_denom_coef | sci_denom_plain).optimize()
        sfc_num_mc = cross("斑点形成细胞", "SFC") | cross("SFC", "SFC")
        sfc_num_pbmc = cross("斑点形成细胞", "SFCs") | cross("SFC", "SFCs") | cross("SFCs", "SFCs")
        sfc_den_mc = delete("每") + insert("/") + sci_scaled_denom + cross("单个核细胞", "MC")
        sfc_den_pbmc = delete("每") + insert("/") + sci_scaled_denom + cross("PBMC", "PBMC")
        sfc_family_body = (sfc_num_mc + sfc_den_mc) | (sfc_num_pbmc + sfc_den_pbmc)
        measure_sfc_family = add_weight(sfc_family_body, -0.57)
        measure_num_sfc_family = add_weight(num_or_ascii + sfc_family_body, -0.57)
        measure_sci_sfc_family = add_weight(delete("一").ques + sci_body_scaled + sfc_family_body, -0.58)
        # SI 分子 + 每 + 10^n（无细胞/血小板后缀），如「纳摩尔每十的七次方」→nmol/10^7
        measure_si_num_per_sci = add_weight(
            (si_num_mol | si_num_g | si_num_u | si_num_iu | si_num_special_u)
            + delete("每")
            + insert("/")
            + delete("一").ques
            + sci_body_scaled,
            -0.56,
        )
        measure_g_per_vol_feu = add_weight(
            si_num_g
            + delete("每")
            + insert("/")
            + si_den_vol
            + (
                cross("纤维蛋白原当量", " FEU")
                | cross("（纤维蛋白原当量单位）", " (FEU)")
            ),
            -0.56,
        )
        measure_si_num_per_num_den = add_weight(
            (si_num_mol | si_num_g | si_num_u | si_num_iu | si_num_special_u | si_num_named_u)
            + delete("每")
            + insert("/")
            + num_or_ascii
            + (si_den_vol | si_den_g),
            -0.56,
        )
        measure_si_hb = add_weight(
            (si_num_u | si_num_iu)
            + delete("每")
            + insert("/")
            + cross("克", "g")
            + delete("血红蛋白")
            + insert("Hb"),
            -0.56,
        )
        measure_special_fixed = add_weight(
            _si_cross(
                ("贝塞斯达单位", "BU"),
                ("百万分之一", "ppm"),
                ("十亿分之一", "ppb"),
                ("达因秒每厘米五次方", "dyn.s/cm5"),
                ("千卡每二十四小时, 千焦每二十四小时", "kcal/24h, kJ/24h"),
            ),
            -0.57,
        )
        sci_num_per_time_suffix = si_num + delete("每") + insert("/") + time_num_rate
        sci_per_time_suffix = delete("每") + insert("/") + time_num_rate
        sci_num_per_m2_suffix = (si_num_triple | vol_flow_num) + delete("每") + insert("/") + area_m2
        sci_count_per_suffix = delete("个").ques + count_per_den
        sci_optional_ge_density_suffix = delete("个").ques + si_density_body
        sci_suffix = (
            add_weight(units_en, -1.0)
            | add_weight(measure_special_fixed, -1.0)
            | add_weight(triple_suffix, -1.1)
            | add_weight(sci_num_per_time_suffix, -1.03)
            | add_weight(sci_per_time_suffix, -1.03)
            | add_weight(sci_num_per_m2_suffix, -1.03)
            | add_weight(sci_count_per_suffix, -1.03)
            | add_weight(sci_optional_ge_density_suffix, -1.03)
            | measure_si_creatinine
            | measure_si_density
        )
        # 有单位后缀时优先（与「十的十二次方每升」）；无后缀时允许纯幂如「十的十二次方」→10^12
        measure_sci = add_weight(delete("一").ques + sci_body + sci_suffix, -0.58) | add_weight(
            delete("一").ques + sci_body, -0.53
        )

        # 百分之三十, 百分三十, 百分之百，百分之三十到四十, 百分之三十到百分之五十五
        percent = (
            (sign + delete("的").ques).ques
            + delete("百分")
            + delete("之").ques
            + (
                (Cardinal().number + (to + Cardinal().number).ques)
                | ((Cardinal().number + to).ques + cross("百", "100"))
            )
            + insert("%")
        )

        # 十千米每小时 => 10km/h, 十一到一百千米每小时 => 11~100km/h
        measure = (
            measure_sci
            | measure_sci_sfc_family
            | measure_si_per_scaled_wbc_rbc
            | measure_num_sfc_family
            | measure_sfc_family
            | measure_sci_lab_acronym_per_vol
            | measure_num_lab_acronym_per_vol
            | measure_lab_acronym_per_vol
            | measure_latin_prefix_u_per_vol
            | measure_si_num_per_sci
            | measure_g_per_vol_feu
            | measure_si_num_per_num_den
            | measure_si_hb
            | measure_special_fixed
            | measure_per_scaled_wbc_rbc
            | measure_per_count_wbc_rbc
            | measure_si_creatinine
            | measure_osm
            | measure_si_density
            | measure_num_si_density
            | measure_num_count_per
            | measure_num_count_per_time
            | measure_per_time_num_count
            | measure_energy_per_time
            | measure_si_per_time
            | measure_per_time
            | measure_num_per_time
            | measure_num_per_m2
            | measure_triple_plain
            | measure_triple
            | (number + (to + number).ques + units)
        )

        # XXX: 特殊case处理, ignore enable_standalone_number
        # digit + union("百", "千", "万") + digit + unit
        unit_sp_case1 = [
            "年",
            "月",
            "个月",
            "周",
            "天",
            "位",
            "次",
            "个",
            "顿",
        ]
        if self.enable_0_to_9:
            measure_sp = add_weight(
                (
                    (digit + delete("百") + add_weight(addzero**2, 1.0))
                    | (digit + delete("千") + add_weight(addzero**3, 1.0))
                    | (digit + delete("万") + add_weight(addzero**4, 1.0))
                )
                + insert(" ")
                + digit
                + union(*unit_sp_case1),
                -0.5,
            )
        else:
            measure_sp = add_weight(
                (
                    (digit + delete("百") + add_weight(addzero**2, 1.0))
                    | (digit + delete("千") + add_weight(addzero**3, 1.0))
                    | (digit + delete("万") + add_weight(addzero**4, 1.0))
                )
                + digit_zh
                + union(*unit_sp_case1),
                -0.5,
            )

        tagger = insert('value: "') + (measure | measure_sp | percent) + insert('"')
        # 每小时十千米 => 10km/h, 每小时三十到三百一十一千米 => 30~311km/h
        tagger |= insert('denominator: "') + delete("每") + units + insert('" numerator: "') + measure + insert('"')

        self.tagger = self.add_tokens(tagger)

    def build_verbalizer(self):
        super().build_verbalizer()
        numerator = delete('numerator: "') + self.SIGMA + delete('"')
        denominator = delete(' denominator: "') + self.SIGMA + delete('"')
        verbalizer = numerator + insert("/") + denominator
        self.verbalizer |= self.delete_tokens(verbalizer)
