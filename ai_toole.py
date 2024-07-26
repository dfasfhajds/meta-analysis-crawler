import os
from openai import OpenAI
import json
import mimetypes
import base64
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.chatanywhere.tech/v1"
)

#Quality assessment related

def get_quality_related_articles(text: str) -> str:
    try:
        messages = [
            {
                'role': "system",
                'content': """
                    You are an expert in analyzing meta-analysis articles. You will receive a caption input which is the first page of the supplementary of a meta-analysis article.
                    Please judge weather this supplementary file contains the quality assessment. Return 1 if it has, otherwise return 0. You can only choose between {1, 0}.
                    Note that risk of bias cannot be regarded as quality assessmentm, you are not allowed to explain anything.
                    Here are some examples:
                    example 1:
                        input:
                            Supplementary Online Content
                            Widyaputri F, Rogers SL, Kandasamy R, Shub A, Symons RCA, Lim LL. Global estimates of
                            diabetic retinopathy prevalence and progression in pregnant women with preexisting diabetes: a
                            systematic review and meta-analysis. JAMA Ophthalmol. Published online March 24, 2022.
                            doi:10.1001/jamaophthalmol.2022.0050
                            eTable 1. Systematic Review Search Strategy
                            eTable 2. Methodological and Reporting Quality Scoring
                            eTable 3. Determination of Score Thresholds for High-Quality Studies
                            eTable 4. Quality Score of Included Studies
                            eTable 5. Characteristics of Pregnant Women in Each Study Population
                            eTable 6. Pooled Prevalence of Proliferative Diabetic Retinopathy Around Delivery
                            eTable 7. Pooled Progression Rate of Nonproliferative Diabetic Retinopathy Worsening by
                            at Least 1 Level
                            eTable 8. Comparison of Pooled Estimates Between Freeman-Tukey Double
                            Arcsine Transformation and Random Intercept Mixed-Effects Logistic Regression
                            Model
                            eFigure 1. Systematic Search and Selection of Eligible Literature
                            eFigure 2. Forest Plots of Prevalence of any DR Using Studies With Similar Quality, by
                            Type of Diabetes
                            eFigure 3. Forest Plots of Prevalence of PDR Using Studies With Similar Quality, by Type
                            of Diabetes
                            eFigure 4. Forest Plots of Prevalence of any DR Using Studies With Similar Quality and
                            DR Grading Scheme, by Diabetes Type
                            eFigure 5. Forest Plots of Prevalence of PDR Using Studies With Similar Quality and DR
                            Grading Scheme, by Type of Diabetes
                            eReferences
                            This supplementary material has been provided by the authors to give readers
                            additional information about their work.
                            © 2022 American Medical Association. All rights reserved.
                        output: 1

                    example 2:
                        input:
                            Supplemental Online Content
                            Patil NS, Mihalache A, Dhoot AS, Popovic MM, Muni RH, Kertes PJ. Association between visual
                            acuity and residual retinal fluid following intravitreal anti–vascular endothelial growth factor
                            treatment for neovascular age-related macular degeneration: a systematic review and meta-
                            analysis. JAMA Ophthalmol. Published online May 12, 2022.
                            doi:10.1001/jamaophthalmol.2022.1357
                            eFigure 1. Flowchart for study selection
                            eFigure 2. Forest plots depicting a monthly treatment regimen subgroup analysis of residual
                            retinal fluid presence at last study observation versus residual retinal fluid absence at last study
                            observation
                            eFigure 3. Forest plots depicting a treat-and-extend treatment regimen subgroup analysis
                            eFigure 4. Forest plots depicting a subgroup analysis of RCTs or post-hoc studies of RCTs
                            eFigure 5. Forest plots depicting a subgroup analysis of observational studies
                            eTable 1. Full search strategy for MEDLINE
                            eTable 2. Risk of bias assessment of included randomized controlled trials using the Cochrane
                            risk of bias tool 2
                            eTable 3. Risk of bias assessment of included observational studies using ROBINS-I
                            eTable 4. Grading of Recommendations, Assessment, Development and Evaluation (GRADE)
                            summary of findings
                            eMethods
                            eResults
                            This supplemental material has been provided by the authors to give readers additional
                            information about their work.
                        output: 0
                    
                    example 3:
                        input:
                            Supplemental Online Content
                            Cho JY, Won YK, Park J, et al. Visual outcomes and optical quality of accommodative, multifocal,
                            extended depth-of-focus, and monofocal intraocular lenses in presbyopia-correcting cataract surgery:
                            a systematic review and bayesian network meta-analysis. JAMA Ophthalmol. Published online
                            September 22, 2022. doi:10.1001/jamaophthalmol.2022.3667
                            eMethods.
                            eFigure 1. PRISMA flow chart of study selection
                            eFigure 2. Traffic light plot for assessing the risk of bias
                            eFigure 3. Pairwise comparison for uncorrected visual acuities
                            eFigure 4. SUCRA for visual acuities
                            eFigure 5. Forest plot for corrected visual acuities compared with monofocal IOL
                            eFigure 6. Pairwise comparison for corrected visual acuities
                            eFigure 7. Pairwise comparison for quality of vision
                            eFigure 8. Forest plot for corrected visual acuities compared with monofocal IOL from the studies
                            without high risk of bias
                            eTable 1. Detailed information regarding network geometry
                            eTable 2. Detailed information on network geometry by treatment
                            eTable 3. Detailed information on network geometry by pairwise comparison
                            eTable 4. Characteristics of included studies in the meta-analysis
                            This supplemental material has been provided by the authors to give readers additional information
                            about their work.
                            © 2022 American Medical Association. All rights reserved.
                        output: 0
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error when prompting gpt-3.5-turbo to find quality related sections: {e}")
        return []

def read_citation(text: str) -> str:
    try:
        messages = [
            {
                'role': "system",
                'content': """
                    You are an expert in analyzing meta-analysis articles. The following information is the table with explanation.
                    Please return the explanation of the various scoring criteria in the table. If there is no explanation return 0 only.
                    Here are some examples:
                        Input:
                            Author S1 S2 S3 S4 C1 C2 O1 O2 O3 Score Wong et al * * * * * 5 Brady et al * * * * * 5 Stafford et al * * * * * 5 
                            Robbins et al * * * * 4 Lutas et al * * * * 4 Buda et al * * * * 4 Erbel et al * * * * 4 Mugge et al * * * * 4 
                            Hwang et al * * * * 4 Jung et al et al * * * * * 5 Werner et al * * * * * 5 De Castro et al * * * * * 5 Di Salvo et al * * * * * * * 7 
                            Vilacosta et al * * * * * * 6 Deprele et al * * * * * * * 7 Thuny et al * * * * * * * 7 Gotsman et al * * * * * * * 7 Pepin et al * * * * * * * 7 
                            Leitman et al * * * * * * * 7 Hajihossainlou * * * * * 5 et al Garcia- * * * * * * * * 8 Cabrera et al Mislfeld et al * * * * * * * * 8 Rizzi et al * * * * * * * 7 
                            Aherrera et al * * * * * * * * 8 aQuality of studies judged on the basis of- representativeness of the exposed cohort (S1); selection of the non-exposed cohort (S2); ascertainment of exposure (S3); 
                            demonstration that the outcome of interest was not present at the start of the study (S4); comparability (C1 and C2); assessment of outcome (E1); was follow-up long enough for outcomes to occur (E2); 
                            adequacy of follow-up of cohorts (E3) © 2018 American Medical Association. All rights reserved.
                        Output: 
                            aQuality of studies judged on the basis of- representativeness of the exposed cohort (S1); selection of the non-exposed cohort (S2); ascertainment of exposure (S3); demonstration that the outcome of interest was not present at the start of the study (S4); comparability (C1 and C2); assessment of outcome (E1); was follow-up long enough for outcomes to occur (E2); adequacy of follow-up of cohorts (E3) ? 2018 American Medical Association. All rights reserved.

                        Input:
                            Kenyon 
                            KR. 1989 
                            R, NC, 
                            CA 
                            CLAU 
                            26 
                            30.8±15 
                            18±11.9  
                            4 
                            C: comparative; CA: case series; CLAL: conjunctival limbal allograft; CLAU: conjunctival limbal 
                            autograft; CLET: cultivated limbal epithelial transplantation; CO: case cohort; KLAL: keratolimbal 
                            allograft; M: months; NC: non-comparative; P: prospective; R: retrospective; SLET; Y: year
                        Output:
                            C: comparative; CA: case series; CLAL: conjunctival limbal allograft; CLAU: conjunctival limbal autograft; CLET: cultivated limbal epithelial transplantation; CO: case cohort; KLAL: keratolimbal allograft; M: months; NC: non-comparative; P: prospective; R: retrospective; SLET; Y: year

                        Input：
                            eTable 1: Assessment of quality of studies using the Newcastle-Ottawa scale
                            Author S1 S2 S3 S4 C1 C2 O1 O2 O3 Score Wong et al * * * * * 5 Brady et al * * * * * 5 Stafford et al * * * * * 5 
                            Robbins et al * * * * 4 Lutas et al * * * * 4 Buda et al * * * * 4 Erbel et al * * * * 4 Mugge et al * * * * 4 
                            Hwang et al * * * * 4 Jung et al et al * * * * * 5 Werner et al * * * * * 5 De Castro et al * * * * * 5 Di Salvo et al * * * * * * * 7 
                            Vilacosta et al * * * * * * 6 Deprele et al * * * * * * * 7 Thuny et al * * * * * * * 7 Gotsman et al * * * * * * * 7 Pepin et al * * * * * * * 7 
                            Leitman et al * * * * * * * 7 Hajihossainlou * * * * * 5 et al Garcia- * * * * * * * * 8
                        Output: 0
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error when prompting gpt-4o to find quality related sections: {e}")
        return []

def judge_quality_assessment(text: str) -> str:
    try:
        messages = [
            {
                'role': "system",
                'content': """
                    You are an expert in analyzing meta-analysis articles. You will receive a string input in the following format:
                        {type_of_table_required} : {given table's title}
                    You need to determine if the {given table's title} belongs to the {type_of_table_required} category. If it does, return 1; otherwise, return 0. You can only choose between {1, 0}.
                    Note that you are not allowed to generate any explanation, only need to return 1 or 0.
                    Here are some examples:
                        Input: Quality Assessment : eTable 4. Quality Score of Included Studies
                        Output: 1

                        Input: Quality Assessment : eTable 1: Assessment of quality of studies using the Newcastle-Ottawa scale
                        Output: 1

                        Input: Quality Assessment : eTable 2. Risk of bias assessment of included randomized controlled trials using the Cochrane risk of bias tool 2
                        Output: 0
                        
                        Input: Quality Assessment : eTable 1 Characteristics of eligible studies and quality assessment
                        OUtput: 1 
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error when prompting gpt-4o to find quality related sections: {e}")
        return []

#Search strategy related

def get_search_strategy_related_article(text: str) -> str:
    try:

        messages = [
            {
                'role': "system",
                'content': """
                You are particularly good at conducting meta-analysis on medicine articles.
                Based on the provided caption of supplementary materials of a meta-analysis,
                find sections that are related to search strategy of the included studies.
                Please judge weather this supplementary file contains the search strategy. Return 1 if it has, otherwise return 0. You can only choose between {1, 0}.
                Note that if the search strategy is presented as an image, we do not consider it to have a search strategy and return 0. You are not allowed to explain anything.
                Here are some examples:
                example 1:
                    input:
                        Supplementary Online Content
                        Widyaputri F, Rogers SL, Kandasamy R, Shub A, Symons RCA, Lim LL. Global estimates of
                        diabetic retinopathy prevalence and progression in pregnant women with preexisting diabetes: a
                        systematic review and meta-analysis. JAMA Ophthalmol. Published online March 24, 2022.
                        doi:10.1001/jamaophthalmol.2022.0050
                        eTable 1. Systematic Review Search Strategy
                        eTable 2. Methodological and Reporting Quality Scoring
                        eTable 3. Determination of Score Thresholds for High-Quality Studies
                        eTable 4. Quality Score of Included Studies
                        eTable 5. Characteristics of Pregnant Women in Each Study Population
                        eTable 6. Pooled Prevalence of Proliferative Diabetic Retinopathy Around Delivery
                        eTable 7. Pooled Progression Rate of Nonproliferative Diabetic Retinopathy Worsening by
                        at Least 1 Level
                        eTable 8. Comparison of Pooled Estimates Between Freeman-Tukey Double
                        Arcsine Transformation and Random Intercept Mixed-Effects Logistic Regression
                        Model
                        eFigure 1. Systematic Search and Selection of Eligible Literature
                        eFigure 2. Forest Plots of Prevalence of any DR Using Studies With Similar Quality, by
                        Type of Diabetes
                        eFigure 3. Forest Plots of Prevalence of PDR Using Studies With Similar Quality, by Type
                        of Diabetes
                        eFigure 4. Forest Plots of Prevalence of any DR Using Studies With Similar Quality and
                        DR Grading Scheme, by Diabetes Type
                        eFigure 5. Forest Plots of Prevalence of PDR Using Studies With Similar Quality and DR
                        Grading Scheme, by Type of Diabetes
                        eReferences
                        This supplementary material has been provided by the authors to give readers
                        additional information about their work.
                        © 2022 American Medical Association. All rights reserved.
                    output: 1
                
                example 2:
                    input:
                        Supplemental Online Content
                        Honkila M, Koskela U, Kontiokari T, et al. Effect of topical antibiotics on duration of acute infective
                        conjunctivitis in children: a randomized clinical trial and a systematic review and meta-analysis.
                        JAMA Netw Open. 2022;5(10):e2234459. doi:10.1001/jamanetworkopen.2022.34459
                        eTable 1. Baseline Characteristics of Participants in the Randomized Clinical Trial
                        eTable 2. Microbiological Findings at Entry
                        eTable 3. Descriptions of the Randomized Clinical Trials Included in the Systematic Review and
                        Meta-analysis
                        eTable 4. Risk of Bias Assessments in the Meta-analysis Material Using the Cochrane
                        Collaboration's Tool for Assessing the Risk of Bias in Randomized Trials
                        eFigure 1. Funnel Plot of Studies Included for Assessment of the Proportion of Participants With
                        Conjunctival Symptoms on Days 3 to 6
                        eFigure 2. Funnel Plot of Studies Included for Assessment of the Proportion of Participants With
                        Conjunctival Symptoms on Days 7 to 10
                        eFigure 3. Funnel Plot of Studies Included for Assessment of the Proportion of Participants Who
                        Had a Positive Bacterial Culture From the Conjunctivae on Days 7 to 10
                        eFigure 4. Proportions of Participants With Conjunctival Symptoms on Days 7 to 10 in Trials
                        Comparing Antibiotics With a Placebo for Treating Acute Conjunctivitis in Children
                        eFigure 5. Proportions of Participants Who Had a Positive Bacterial Culture From the Conjunctivae
                        on Days 7 to 10 in Trials Comparing Antibiotics With a Placebo for Treating Acute Conjunctivitis in
                        Children
                        This supplemental material has been provided by the authors to give readers additional information
                        about their work.
                        © 2022 Honkila M et al. JAMA Network Open.
                    output: 0
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error when prompting gpt-3.5-turbo to find quality related sections: {e}")
        return []
    
def judge_strategy(text: str) -> str:
    try:

        messages = [
            {
                'role': "system",
                'content': """
                    You are an expert in analyzing meta-analysis articles. You will receive a string input in the following format:
                        {type_of_table_required} : {given table's title}
                    You need to determine if the {given table's title} belongs to the {type_of_table_required} category. If it does, return 1; otherwise, return 0. You can only choose between {1, 0}.
                    Note that you are not allowed to generate any explanation, only need to return 1 or 0.
                    Here are some examples:
                        Input: Search Strategy : eTable 1. Systematic Review Search Strategy
                        Output: 1

                        Input: Search Strategy : eFigure 1. Systematic Search and Selection of Eligible Literature 
                        Output: 0
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error when prompting gpt-4o to find quality related sections: {e}")
        return []

def generate_search_strategy(text: str) -> str:
    try:

        messages = [
            {
                'role': "system",
                'content': """
                    You are good at analyzing the search strategy table in meta-analysis.
                    Please generate a query string for this search strategy based on the search steps and logical
                    operators in the table, which will be used in coding. Note that you only need to generate the search strategy. 
                    Note that you are only allowed to generate search strategy without any explanation. You should avoid blank lines.
                    Here is an example:
                    input:  Databases 
                            Medline/OVID 1 diabetic retinopathy.ti,ab. or diabetic retinopathy/ti, ab or diabetic retinopathy/
                            2 (pregnant or pregnancy).ti,ab. or pregnancy/
                            3 1 AND 2
                            4 limit 3 to (english language and humans)
                            5 limit 4 to (clinical study or clinical trial, all or clinical trial, phase i or clinical trial, phase ii or clinical trial, phase iii or clinical trial,      
                            phase iv or clinical trial or comparative study or controlled clinical trial or journal article or multicenter study or observational study
                            or pragmatic clinical trial or randomized controlled trial or twin study)

                            EMBASE/OVID 1 diabetic retinopathy.ti,ab. or diabetic retinopathy/ti, ab or diabetic retinopathy/
                            2 (pregnant or pregnancy).ti,ab. or pregnancy/
                            3 1 AND 2
                            4 limit 3 to (human and english language and embase)
                            5 limit 4 to (article and journal)

                            Scopus 1 TITLE-ABS-KEY ("diabetic retinopathy")
                            2 TITLE-ABS-KEY (pregnant OR pregnancy)
                            3 #1 AND #2
                            4 #3 (LIMIT-TO (DOCTYPE , "ar")) AND (LIMIT-TO(SRCTYPE,"j")) AND (LIMIT-TO (LANGUAGE, "English"))
                    output:
                            (Diabetic retinopathy[Title/Abstract] OR 
                            Diabetic retinopath*[Title/Abstract] OR 
                            diabetic retinal disease[Title/Abstract] OR 
                            diabetic macular oedema*[Title/Abstract] OR 
                            DMO[Title/Abstract] OR DME[Title/Abstract]) AND 
                            ("quality of life"[Title/Abstract] OR 
                            qol[Title/Abstract] OR hrqol[Title/Abstract] OR 
                            "health related quality of life"[Title/Abstract] OR 
                            eq5d[Title/Abstract] OR eq-5d[Title/Abstract]) AND 
                            ((vision[Title/Abstract] OR visual[Title/Abstract] OR ocular[Title/Abstract]) AND 
                            (function*[Title/Abstract] OR quality[Title/Abstract])) OR 
                            (Quality of vision[Title/Abstract] OR NEI-VFQ-25[Title/Abstract] OR vfq-25[Title/Abstract] OR vfq[Title/Abstract])
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error when prompting gpt-4o to find quality related sections: {e}")
        return []
