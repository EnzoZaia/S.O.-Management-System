from rest_framework.response import Response
from rest_framework import status


def resposta_sucesso(mensagem, dados=None, status_code=status.HTTP_200_OK):
    return Response({"status": "sucesso", "mensagem": mensagem, "dados": dados}, status=status_code)


def resposta_erro(mensagem, erros=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"status": "erro", "mensagem": mensagem, "erros": erros}, status=status_code)