from django.db import connection, transaction
from itertools import groupby
from operator import itemgetter

def getAllAgendaPartyVotes():
    cursor = connection.cursor()
    cursor.execute(QUERY)
    results = dict(map(lambda (key,group):(key,map(lambda g:(g[1],g[2]),list(group))),
                       groupby(cursor.fetchall(),key=itemgetter(0))))
    return results

QUERY = """
SELECT a.agendaid, 
       a.partyid, 
       round(coalesce(v.totalvotevalue,0)/a.totalscore*100,2) score 
FROM   (SELECT agid                   agendaid, 
               m.id                   partyid, 
               sc * m.number_of_seats totalscore 
        FROM   (SELECT agenda_id               agid, 
                       SUM(abs(score * importance)) sc 
                FROM   agendas_agendavote 
                GROUP  BY agenda_id) agendavalues 
               left outer join mks_party m 
                 ) a 
       left outer join (SELECT agenda_id, 
                          partyid, 
                          SUM(forvotes) - SUM(againstvotes) totalvotevalue 
                   FROM   (SELECT a.agenda_id, 
                                  p.partyid, 
                                  CASE p.vtype 
                                    WHEN 'for' THEN p.numvotes * a.VALUE 
                                    ELSE 0 
                                  END forvotes, 
                                  CASE p.vtype 
                                    WHEN 'against' THEN p.numvotes * a.VALUE 
                                    ELSE 0 
                                  END againstvotes 
                           FROM   (SELECT m.current_party_id      partyid, 
                                          v.vote_id voteid, 
                                          v.TYPE    vtype, 
                                          COUNT(*)  numvotes 
                                   FROM   laws_voteaction v 
                                          inner join mks_member m 
                                            ON v.member_id = m.id 
                                   WHERE  v.TYPE IN ( 'for', 'against' ) 
                                   GROUP  BY m.current_party_id, 
                                             v.vote_id, 
                                             v.TYPE) p 
                                  inner join (SELECT vote_id, 
                                                     agenda_id, 
                                                     score * importance VALUE 
                                              FROM   agendas_agendavote) a 
                                    ON p.voteid = a.vote_id) 
                   GROUP  BY agenda_id, 
                             partyid 
                             ) v 
         ON a.agendaid = v.agenda_id 
            AND a.partyid = v.partyid 
ORDER BY agendaid,score desc"""
