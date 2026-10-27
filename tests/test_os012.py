from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.workspace import review_add,review_remove,review_list,collection_add,collection_list,collection_paths

def main():
    with TemporaryDirectory() as folder:
        db=Path(folder)/"workspace.db"
        a=str(Path(folder)/"one.mp4")
        b=str(Path(folder)/"two.mp4")
        review_add(db,a);review_add(db,a);review_add(db,b)
        assert set(review_list(db))=={a,b}
        collection_add(db,"Trabalho",[a,b])
        assert collection_list(db)==[("Trabalho",2)]
        assert collection_paths(db,"Trabalho")==sorted([a,b])
        review_remove(db,a)
        assert review_list(db)==[b]
        assert set(collection_paths(db,"Trabalho"))=={a,b}
    print("OS012 persistent review and collection safety passed")

if __name__=="__main__":
    main()
