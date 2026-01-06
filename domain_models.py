import uuid
from typing import List
from datetime import datetime


class User:
    """
    Represents a user. Uses encapsulation for the ID.
    """
    def __init__(self,username: str,email: str):
        self._id=str(uuid.uuid4())
        self.username=username
        self.email=email
        self.created_at=datetime.now()
    
    @property
    def id(self)->str:
        return self._id
    
    def __repr__(self):
        return f"<User(id={self._id} , username='{self.username}', email='{self.email}')>"





class Document:
    """
    Represents a document. Linked to a specific User.
    """
    def __init__(self,title: str,content: str,uploader: User):
        self._id=str(uuid.uuid4())
        self.title=title
        self.content=content
        self.uploader=uploader
        self.uploaded_at=datetime.now()
    
    @property
    def id(self)->str:
        return self._id
    
    def __repr__(self):
        return f"<Document(title : {self.title}, owner : {self.uploader.username} )>"


class DocumentStore:
    """
    In-memory database manager for Users and Documents.
    """
    def __init__(self):
        self._users: List[User]=[]
        self._documents: List[Document]=[]
    
    def add_user(self,user : User) -> None:
        if any(u.email==user.email for u in self._users):
            raise ValueError(f"User with email : {user.email} already exists")
        
        self._users.append(user)
        print(f"User: {user.username} added succesfully")

    def add_document(self,document: Document) -> None:
        if document.uploader not in self._users:
            raise ValueError(f"Document uploader is not registered")


        self._documents.append(document)
        print(f"Document {document.title} added successfully")

    def get_user_documents(self,user_id: str)->List[Document]:
        result=[]
        for doc in self._documents:
            if doc.uploader.id==user_id:
                result.append(doc)
        
        return result


#Tests
if __name__=="__main__":

    store=DocumentStore()

    # Create and Add User
    user1=User(username="Vishnu Bhargav",email="bhargav@gmail.com")
    store.add_user(user1)

    # Create and add Document
    doc1=Document(title="LangGraph",content="blah blah...",uploader=user1)
    store.add_document(doc1)

    store.get_user_documents(user1._id)

