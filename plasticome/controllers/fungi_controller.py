from ..services.genbank_service import search_fungi_id_by_name


def search_fungi_by_name(fungi_name: str):
    """
    The function `search_fungi_by_name` searches for fungi genomes by name and
    returns the corresponding GenBank and RefSeq assembly accessions.

    :param fungi_name: The parameter `fungi_name` is a string that represents the
    name of the fungi you want to search for
    :type fungi_name: str
    :return: a dictionary containing the GenBank assembly accession and RefSeq
    assembly accession of the fungi, along with a status code of 200 if the genome
    is found. If the genome is not found, it returns a dictionary with a message
    indicating that the genome was not found, along with a status code of 404.
    """
    genbank_accession, refseq_accession = search_fungi_id_by_name(fungi_name)
    if genbank_accession or refseq_accession:
        return {
            'genbank_assembly_accession': genbank_accession,
            'refseq_assembly_accession': refseq_accession,
        }, 200
    return {'message': 'Genome not found'}, 404
