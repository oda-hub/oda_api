import rdflib as rdf
from rdflib.collection import Collection
from rdflib.namespace import RDF, RDFS, OWL, XSD
import logging
import builtins
from copy import deepcopy

try:
    from cdci_data_analysis.analysis.exceptions import RequestNotUnderstood
    # special treatment of this exception when working with dispatcher 
except ImportError:
    class RequestNotUnderstood(RuntimeError): pass # type: ignore[no-redef]


logger = logging.getLogger(__name__)

ODA = rdf.Namespace("http://odahub.io/ontology#")
ODAS = rdf.Namespace("https://odahub.io/ontology#")
a = RDF.type

def xsd_type_to_python_type(xsd_uri):
    # TODO: this works only with simple builtin types, but OK for now
    typename = str(xsd_uri).split('#')[-1]
    if typename == 'integer': typename = 'int'
    if typename == 'boolean': typename = 'bool'
    if typename == 'string': typename = 'str'
    try:
        return getattr(builtins, typename)
    except AttributeError:
        return None

class MainOntologyGraph:
    def __init__(self, ontology_path, version):
        self._ver = version 
        self._path = ontology_path
        self._g = rdf.Graph()
        self._g.parse(ontology_path)
        self._g.bind('oda', ODA)
        self._g.bind('odas', ODAS)
        
    @property
    def ontology_path(self):
        return self._path
    
    @property 
    def version(self):
        return self._ver
    
    @property
    def graph(self):
        return deepcopy(self._g)
    
    def reset(self, ontology_path, version):
        if version != self._ver or ontology_path != self._path:
            self._g = rdf.Graph()
            self._g.parse(ontology_path)
            self._g.bind('oda', ODA)
            self._g.bind('odas', ODAS)
            self._path = ontology_path
            self._ver = version 

main_ontology_graph = None

class Ontology:
    def __init__(self, ontology_path):
        global main_ontology_graph
        if main_ontology_graph is None:
            main_ontology_graph = MainOntologyGraph(ontology_path, '0') 
        self.g = main_ontology_graph.graph
        # NOTE: the main ontology graph is initialized in first call and then persist 
        #       this reduces amount of ttl parsing and requests if it's read from remote
        #       every instance will reuse the copy of it 
        # TODO: ontology versioning; method to update graph
        
    def _get_symb(self, uri):
        s_qres = self.g.query( """SELECT ?symb WHERE { 
                                  { <%s> oda:symbol ?symb } 
                                    UNION
                                  { <%s> rdfs:label ?symb }
                                } """ % (uri, uri) 
                            )
        if len(s_qres) == 0: return uri.split('#')[1]
        return str(list(s_qres)[0][0])
    
    def parse_oda_annotations(self, graph):
        """
        will account for class annotations, which have special meaning
        (currently lower_limit, upper_limit, allowed_value, unit, format)
        producing respective owl class restrictions
        """

        #TODO: duplicates restrictions if they already set
        #       not a problem for extra_ttl 
        #       but may occur in reparsing "big" ontology (not needed now)
    
        self.parse_unit_annotations(graph)
        self.parse_format_annotations(graph)
        self.parse_allowed_values_annotations(graph)
        self.parse_limits_annotations(graph, infer_datatype=True)
        
        
        
    def parse_unit_annotations(self, graph):  
        for classuri in graph.subjects(ODA['unit'], None):
            unit_annotations = list(graph.objects(classuri, ODA['unit']))
            if len(unit_annotations) > 1: 
                raise RuntimeError('Multiple oda:unit annotations for %s', classuri)
            for unituri in unit_annotations:
                bn = rdf.BNode()
                graph.add((bn, a, OWL.Restriction))
                graph.add((bn, OWL.onProperty, ODA.has_unit))
                graph.add((bn, OWL.hasValue, unituri))
            
                graph.add((classuri, RDFS.subClassOf, bn))
            
    def parse_format_annotations(self, graph):
        for classuri in graph.subjects(ODA['format'], None):
            format_annotations = list(graph.objects(classuri, ODA['format']))
            if len(format_annotations) > 1: 
                raise RuntimeError('Multiple oda:format annotations for %s', classuri)
            for formaturi in format_annotations:
                bn = rdf.BNode()
                graph.add((bn, a, OWL.Restriction))
                graph.add((bn, OWL.onProperty, ODA.has_format))
                graph.add((bn, OWL.hasValue, formaturi))
                
                graph.add((classuri, RDFS.subClassOf, bn))
            
    def parse_allowed_values_annotations(self, graph):        
        for classuri in graph.subjects(ODA['allowed_value'], None, unique=True):
            c = Collection(graph, None)
            for val in graph.objects(classuri, ODA['allowed_value']):
                c.append(val)
                
            dtype = rdf.BNode()
            graph.add((dtype, a, RDFS.Datatype))
            graph.add((dtype, OWL.oneOf, c.uri))
                
            bn = rdf.BNode()
            graph.add((bn, a, OWL.Restriction))
            graph.add((bn, OWL.onProperty, ODA.value))
            graph.add((bn, OWL.allValuesFrom, dtype))
            
            graph.add((classuri, RDFS.subClassOf, bn))
            
    def parse_limits_annotations(self, graph, infer_datatype = True):        
        with_lower = list(graph.subjects(ODA['lower_limit'], None, unique=True))
        with_upper = list(graph.subjects(ODA['upper_limit'], None, unique=True))
        
        for classuri in set(with_lower + with_upper):
            ll = list(graph.objects(classuri, ODA['lower_limit']))
            ul = list(graph.objects(classuri, ODA['upper_limit']))
            if len(ll) > 1: 
                raise RuntimeError('Multiple oda:lower_limit annotations for %s', classuri)
            if len(ul) > 1: 
                raise RuntimeError('Multiple oda:lower_limit annotations for %s', classuri)
            
            limits_datatype = XSD.float # default, will work in most current cases
            if infer_datatype:
                # graph will usually be separate graph, 
                # here, try to get datatype restriction for directly defined superclasses
                possible_datatypes = set()
                superclasses = list(graph.objects(classuri, RDFS.subClassOf))
                superclasses.append(classuri)
                for sc in superclasses:
                    if isinstance(sc, rdf.BNode): continue
                    dt = self._get_datatype_restriction(sc)
                    if dt is not None:
                        possible_datatypes.add(dt)
                if len(possible_datatypes) > 1:
                    raise RuntimeError('Ambiguous datatype for %s', classuri)
                if len(possible_datatypes) == 1:
                    limits_datatype = list(possible_datatypes)[0]
            
            lim_r = []
            if len(ll) != 0:
                lim_r.append(rdf.BNode())
                graph.add((lim_r[-1], 
                           XSD.minInclusive, 
                           rdf.Literal(xsd_type_to_python_type(limits_datatype)(ll[0].value), 
                                       datatype=limits_datatype)))
            if len(ul) != 0:
                lim_r.append(rdf.BNode())
                graph.add((lim_r[-1], 
                           XSD.maxInclusive, 
                           rdf.Literal(xsd_type_to_python_type(limits_datatype)(ul[0].value), 
                                       datatype=limits_datatype)))
            c = Collection(graph, None, lim_r)
                        
            dtype = rdf.BNode()
            graph.add((dtype, a, RDFS.Datatype))
            graph.add((dtype, OWL.onDatatype, limits_datatype))
            graph.add((dtype, OWL.withRestrictions, c.uri))
            
            bn = rdf.BNode()
            graph.add((bn, a, OWL.Restriction))
            graph.add((bn, OWL.onProperty, ODA.value))
            graph.add((bn, OWL.allValuesFrom, dtype))
            
            graph.add((classuri, RDFS.subClassOf, bn))
    
    def _get_datatype_restriction(self, param_uri):
        param_uri = f"<{param_uri}>" if param_uri.startswith("http") else param_uri
        query = """
            SELECT ?dt WHERE {
                {
                    %s rdfs:subClassOf+ [
                        a owl:Restriction ;
                        owl:onProperty oda:value ;
                        owl:allValuesFrom ?dt
                    ]   
                    FILTER(isUri(?dt) && STRSTARTS(STR(?dt), STR(xsd:)))
                }
                UNION
                {
                    BIND(%s as ?dt)
                    FILTER(STRSTARTS(STR(%s), STR(xsd:)))
                }
                UNION
                {
                    %s rdfs:subClassOf+ ?dt .
                    FILTER(isUri(?dt) && STRSTARTS(STR(?dt), STR(xsd:)))
                }
            }
        """ % (param_uri, param_uri, param_uri, param_uri)
        qres = list(self.g.query(query))
        if len(qres) == 0: return None
        if len(set(r[0] for r in qres)) > 1:
            raise RuntimeError("Ambiguous datatype of %s", param_uri) 
        return qres[0][0]
    
    def parse_extra_triples(self, extra_triples, format='n3', parse_oda_annotations = True):
        if parse_oda_annotations:
            tmpg = rdf.Graph()
            tmpg.parse(data = extra_triples)       
            try:
                self.parse_oda_annotations(tmpg)
            except RuntimeError as e:
                raise RequestNotUnderstood(str(e))
            extra_triples = tmpg.serialize(format=format)
        self.g.parse(data = extra_triples, format = format)
            
        
    def get_parameter_hierarchy(self, param_uri):
        param_uri_m = f"<{param_uri}>" if param_uri.startswith("http") else param_uri
        query = """
        select ?mid ( count(?mid2) as ?midcount ) where { 
        %s  (rdfs:subClassOf|a)* ?mid . 
        
        ?mid rdfs:subClassOf* ?mid2 .
        ?mid2 rdfs:subClassOf* oda:WorkflowParameter .
        }
        group by ?mid
        order by desc(?midcount)
        """ % ( param_uri_m )

        qres = self.g.query(query)
        
        hierarchy = [str(row[0]) for row in qres]
        if len(hierarchy) > 0:
            return hierarchy  
        else:
            logger.warning("%s is not in ontology or not an oda:WorkflowParameter", param_uri)
            return [ param_uri ]
        
    def get_parameter_format(self, param_uri, return_uri = False):
        if param_uri.startswith("http"): param_uri = f"<{param_uri}>"
       
        query = """ SELECT ?format_uri WHERE { 
            %s (rdfs:subClassOf|a)* [
            a owl:Restriction ;
            owl:onProperty oda:has_format ;
            owl:hasValue ?format_uri ;
            ]
        }
        """ % (param_uri)

        qres = self.g.query(query)
        
        if len(qres) > 1:
            raise RequestNotUnderstood('Ambiguous format for owl_uri ', param_uri) 
        
        if len(qres) == 0: return None
        
        uri = str(list(qres)[0][0])
        if not return_uri:
            return self._get_symb(uri)
        return uri
        
    def get_parameter_unit(self, param_uri, return_uri = False):
        if param_uri.startswith("http"): param_uri = f"<{param_uri}>"

        query = """SELECT ?unit_uri WHERE {
        %s (rdfs:subClassOf|a)* [
            a owl:Restriction ;
            owl:onProperty oda:has_unit ;
            owl:hasValue ?unit_uri ;
            ]
        }
        """ % (param_uri)
        
        qres = self.g.query(query)
        if len(qres) > 1:
            raise RequestNotUnderstood('Ambiguous unit for owl_uri ', param_uri) 
        
        if len(qres) == 0: return None
        
        uri = str(list(qres)[0][0])
        
        if not return_uri:
            return self._get_symb(uri)        
        return uri
        
    def get_limits(self, param_uri):
        if param_uri.startswith("http"): param_uri = f"<{param_uri}>"

        query = """  
            SELECT ?lim WHERE {
            %s rdfs:subClassOf* [
                a owl:Restriction ;
                owl:onProperty oda:value ;
                    owl:allValuesFrom [
                        a rdfs:Datatype ;
                        owl:withRestrictions [ rdf:rest*/rdf:first [ ?side ?lim ] ]        
                    ]
            ] .
            FILTER(?side = xsd:%sInclusive)
            }
        """

        qres_ll = self.g.query(query % (param_uri, 'min'))
        qres_ul = self.g.query(query % (param_uri, 'max'))
        
        if len(qres_ll) == 0: 
            ll = None
        else:
            ll = max([row[0].value for row in qres_ll])
            
        if len(qres_ul) == 0: 
            ul = None
        else:
            ul = min([row[0].value for row in qres_ul])
            
        return (ll, ul)
    
    def get_allowed_values(self, param_uri):
        if param_uri.startswith("http"): param_uri = f"<{param_uri}>"
        
        query = """ SELECT ?item (count(?list) as ?midcount) WHERE {    
            
            ?list rdf:rest*/rdf:first ?item .
                
            %s rdfs:subClassOf* [
                a owl:Restriction ;
                owl:onProperty oda:value ;
                owl:allValuesFrom [
                        a rdfs:Datatype ;
                        owl:oneOf ?list        
                    ]
                ] 
            }
            GROUP BY ?item
            ORDER BY DESC(?midcount)
            """ % param_uri

        qres = self.g.query(query)
        
        repnum = [row[1].value for row in qres]
        if len(repnum) == 0: 
            return None
        maxrep = max(repnum)
        return [row[0].value for row in qres if row[1].value == maxrep]
    
    def get_parprod_terms(self):
        query = """
            SELECT ?s WHERE {
                ?s (rdfs:subClassOf|a)* ?mid0.
                ?mid0 rdfs:subClassOf* oda:DataProduct. 

                ?s (rdfs:subClassOf|a)* ?mid1.
                ?mid1 rdfs:subClassOf* oda:WorkflowParameter .
            }
            GROUP BY ?s
            """
        qres = self.g.query(query)
        return [str(row[0]) for row in qres]
    
    def get_oda_label(self, param_uri):
        if param_uri.startswith("http"): param_uri = f"<{param_uri}>"

        query = "SELECT ?label WHERE {%s oda:label ?label}" % (param_uri)
        
        qres = self.g.query(query)
   
        if len(qres) == 0: return None
        
        label = " ".join([str(x[0]) for x in qres])
        
        return label

    def is_data_product(self, owl_uri, include_parameter_products=True):
        if owl_uri.startswith("http"): owl_uri = f"<{owl_uri}>"
        
        filt_param = 'MINUS{?cl rdfs:subClassOf* oda:ParameterProduct. }' if not include_parameter_products else ''
        query = """
                SELECT (count(?cl) as ?count) WHERE {
                    VALUES ?cl { %s } 
                    ?cl rdfs:subClassOf* oda:DataProduct. 
                    %s
                }
                """ % (owl_uri, filt_param)
        qres = self.g.query(query)
        
        if int(list(qres)[0][0]) == 0: return False
        
        return True    