from collect_safety_health import *
import urllib.parse
# Published survey results, all questions and all-student strata; districts remain districts.
locs=['NYC','LO','CH','HO','PH','SA','DA','FW','DU','CM','SF','SE','DN','NS','DCB','CC','BO']
def getloc(loc):
 params=dict(locations=loc,questions=','.join(r['QuestionCode'] for r in json.loads((RAW/'yrbs_questions.json').read_text()) if r['QuestionType']=='Question'),years='2021,2023,2025',genders='S1',ethnicities='R1',grades='G1',sexualIdentities='I1',sexualContacts='P1',sexualAndGenderIdentities='L1',transgenders='N1',ages='A1')
 return fetch(('S12','https://youthonline.cdc.gov/api/yol/content/highschool?'+urllib.parse.urlencode(params),f'yrbs_results_{loc}.json','school district','2021,2023,2025'))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:list(ex.map(getloc,locs))
