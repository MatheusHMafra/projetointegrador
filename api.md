# Documentação da API do Sistema de Gestão de Estoque

Esta documentação lista todas as rotas da API disponíveis no sistema de gestão de estoque, organizadas por módulo.

## Índice

- [Autenticação](#autenticação)
- [Produtos](#produtos)
- [Categorias](#categorias)
- [Estoque](#estoque)
- [Vendas](#vendas)
- [Fornecedores](#fornecedores)
- [Dashboard](#dashboard)

## Autenticação

### Login

- **URL**: `/auth/login`
- **Método**: `POST`
- **Descrição**: Autentica um usuário no sistema
- **Corpo da Requisição**:

  ```json
  {
    "email": "usuario@exemplo.com",
    "senha": "senha123"
  }
  ```

- **Resposta de Sucesso**:

  ```json
  {
    "authenticated": true,
    "user": {
      "id": 1,
      "nome": "Nome do Usuário",
      "email": "usuario@exemplo.com",
      "nivel_acesso": "admin"
    }
  }
  ```

### Verificar Autenticação

- **URL**: `/auth/check`
- **Método**: `GET`
- **Descrição**: Verifica se o usuário está autenticado
- **Resposta de Sucesso**:

  ```json
  {
    "authenticated": true,
    "user": {
      "id": 1,
      "nome": "Nome do Usuário",
      "email": "usuario@exemplo.com",
      "nivel_acesso": "admin"
    }
  }
  ```

### Logout

- **URL**: `/auth/logout`
- **Método**: `GET`
- **Descrição**: Encerra a sessão do usuário

## Produtos

### Listar Produtos

- **URL**: `/produtos`
- **Método**: `GET`
- **Parâmetros de Query**:
  - `page` (int): Número da página
  - `per_page` (int): Itens por página
  - `categoria_id` (int, opcional): Filtrar por categoria
- **Resposta de Sucesso**:

  ```json
  {
    "produtos": [
      {
        "id": 1,
        "codigo": "P123456",
        "nome": "Nome do Produto",
        "descricao": "Descrição do produto",
        "preco": 99.90,
        "categoria": {"id": 1, "nome": "Categoria"},
        "estoque": 50,
        "estoque_minimo": 10,
        "imagem_url": "/static/uploads/produto.jpg"
      }
    ],
    "total": 100,
    "pages": 10,
    "page": 1,
    "per_page": 10
  }
  ```

### Adicionar Produto

- **URL**: `/produtos`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "nome": "Novo Produto",
    "categoria_id": 1,
    "preco": 99.90,
    "preco_compra": 50.00,
    "estoque": 20,
    "estoque_minimo": 5,
    "descricao": "Descrição do produto"
  }
  ```

- **Resposta de Sucesso**:

  ```json
  {
    "message": "Produto adicionado com sucesso",
    "produto": {
      "id": 10,
      "codigo": "P123456",
      "nome": "Novo Produto",
      "preco": 99.90,
      "estoque": 20
    }
  }
  ```

### Detalhar Produto

- **URL**: `/produtos/<id>`
- **Método**: `GET`
- **Descrição**: Obtém detalhes de um produto específico
- **Resposta de Sucesso**:

  ```json
  {
    "id": 1,
    "codigo": "P123456",
    "nome": "Nome do Produto",
    "descricao": "Descrição do produto",
    "categoria": {"id": 1, "nome": "Categoria"},
    "fornecedor": {"id": 1, "nome": "Fornecedor"},
    "preco": 99.90,
    "preco_compra": 50.00,
    "estoque": 50,
    "estoque_minimo": 10,
    "imagem_url": "/static/uploads/produto.jpg",
    "data_criacao": "27/04/2025 20:06"
  }
  ```

### Atualizar Produto

- **URL**: `/produtos/<id>`
- **Método**: `PUT`
- **Corpo da Requisição**: Campos a serem atualizados
- **Resposta de Sucesso**:

  ```json
  {
    "message": "Produto atualizado com sucesso",
    "produto": {
      "id": 1,
      "nome": "Nome Atualizado",
      "preco": 109.90,
      "estoque": 45
    }
  }
  ```

### Excluir Produto

- **URL**: `/produtos/<id>`
- **Método**: `DELETE`
- **Descrição**: Remove um produto (apenas administradores)
- **Resposta de Sucesso**:

  ```json
  {
    "message": "Produto excluído com sucesso"
  }
  ```

### Buscar Produtos

- **URL**: `/produtos/busca`
- **Método**: `GET`
- **Parâmetros de Query**:
  - `q` (string): Termo de busca
- **Descrição**: Pesquisa rápida de produtos

## Categorias

### Listar Categorias

- **URL**: `/categorias`
- **Método**: `GET`
- **Descrição**: Retorna a lista de categorias de produtos
- **Resposta de Sucesso**:

  ```json
  {
    "categorias": [
      {
        "id": 1,
        "nome": "Eletrônicos"
      },
      {
        "id": 2,
        "nome": "Móveis"
      }
    ]
  }
  ```

### Criar Categoria

- **URL**: `/categorias`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "nome": "Nova Categoria"
  }
  ```

- **Resposta de Sucesso**:

  ```json
  {
    "id": 3,
    "nome": "Nova Categoria"
  }
  ```

### Atualizar Categoria

- **URL**: `/categorias/<id>`
- **Método**: `PUT`
- **Corpo da Requisição**:

  ```json
  {
    "nome": "Nome Atualizado"
  }
  ```

### Excluir Categoria

- **URL**: `/categorias/<id>`
- **Método**: `DELETE`
- **Descrição**: Exclui uma categoria (se não tiver produtos associados)

## Estoque

### Registrar Entrada

- **URL**: `/estoque/entrada`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "produto_id": 1,
    "quantidade": 10,
    "observacao": "Reposição de estoque"
  }
  ```

- **Resposta de Sucesso**:

  ```json
  {
    "message": "Entrada registrada com sucesso",
    "produto": {
      "id": 1,
      "nome": "Nome do Produto",
      "codigo": "P123456",
      "estoque_atual": 60
    }
  }
  ```

### Registrar Saída

- **URL**: `/estoque/saida`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "produto_id": 1,
    "quantidade": 5,
    "observacao": "Saída para exposição"
  }
  ```

- **Resposta de Sucesso**:

  ```json
  {
    "message": "Saída registrada com sucesso",
    "produto": {
      "id": 1,
      "nome": "Nome do Produto",
      "codigo": "P123456",
      "estoque_atual": 55
    }
  }
  ```

### Ajustar Estoque

- **URL**: `/estoque/ajuste`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "produto_id": 1,
    "novo_estoque": 50,
    "observacao": "Correção após inventário"
  }
  ```

- **Descrição**: Ajusta o estoque para um valor específico (apenas admin/gerente)

### Listar Movimentações

- **URL**: `/estoque/movimentacoes`
- **Método**: `GET`
- **Parâmetros de Query**:
  - `page` (int): Número da página
  - `per_page` (int): Itens por página
  - `produto_id` (int, opcional): Filtrar por produto
  - `tipo` (string, opcional): Filtrar por tipo (entrada, saida, ajuste, venda)
- **Descrição**: Lista movimentações de estoque
- **Resposta de Sucesso**:

  ```json
  {
    "movimentacoes": [
      {
        "id": 1,
        "produto": {
          "id": 1,
          "nome": "Nome do Produto",
          "codigo": "P123456"
        },
        "usuario": {
          "id": 1,
          "nome": "Nome do Usuário"
        },
        "tipo": "entrada",
        "quantidade": 10,
        "estoque_anterior": 50,
        "estoque_atual": 60,
        "observacao": "Reposição de estoque",
        "data": "27/04/2025 20:06:00"
      }
    ],
    "total": 100,
    "pages": 10,
    "page": 1
  }
  ```

### Página de Movimentações

- **URL**: `/estoque/movimentacoes/page`
- **Método**: `GET`
- **Descrição**: Renderiza a página de movimentações de estoque

## Vendas

### Listar Vendas

- **URL**: `/estoque/vendas`
- **Método**: `GET`
- **Parâmetros de Query**:
  - `page` (int): Número da página
  - `per_page` (int): Itens por página
- **Descrição**: Lista as vendas registradas
- **Resposta de Sucesso**:

  ```json
  {
    "vendas": [
      {
        "id": 1,
        "codigo": "V20250427ABC1",
        "cliente_nome": "Cliente Teste",
        "valor_total": 299.90,
        "valor_final": 279.90,
        "usuario_id": 1,
        "usuario_nome": "Nome do Usuário",
        "data_venda": "27/04/2025 20:06"
      }
    ],
    "total": 50,
    "pages": 3,
    "page": 1
  }
  ```

### Registrar Venda

- **URL**: `/estoque/vendas`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "cliente_nome": "Cliente Teste",
    "itens": [
      {
        "produto_id": 1,
        "quantidade": 2,
        "preco_unitario": 99.95
      },
      {
        "produto_id": 3,
        "quantidade": 1,
        "preco_unitario": 100.00
      }
    ],
    "desconto": 20.00,
    "forma_pagamento": "cartão",
    "observacao": "Venda para cliente fidelidade"
  }
  ```

- **Resposta de Sucesso**:

  ```json
  {
    "message": "Venda realizada com sucesso!",
    "venda": {
      "id": 1,
      "codigo": "V20250427ABC1",
      "valor_final": 279.90
    }
  }
  ```

### Detalhes de Venda

- **URL**: `/estoque/vendas/<id>`
- **Método**: `GET`
- **Descrição**: Obtém detalhes de uma venda específica
- **Resposta de Sucesso**:

  ```json
  {
    "id": 1,
    "codigo": "V20250427ABC1",
    "cliente_nome": "Cliente Teste",
    "valor_total": 299.90,
    "desconto": 20.00,
    "valor_final": 279.90,
    "forma_pagamento": "cartão",
    "observacao": "Venda para cliente fidelidade",
    "data_venda": "27/04/2025 20:06",
    "usuario": "Nome do Usuário",
    "itens": [
      {
        "id": 1,
        "produto_id": 1,
        "produto_nome": "Nome do Produto",
        "produto_codigo": "P123456",
        "quantidade": 2,
        "preco_unitario": 99.95,
        "subtotal": 199.90
      },
      {
        "id": 2,
        "produto_id": 3,
        "produto_nome": "Outro Produto",
        "produto_codigo": "P789012",
        "quantidade": 1,
        "preco_unitario": 100.00,
        "subtotal": 100.00
      }
    ]
  }
  ```

### Cancelar Venda

- **URL**: `/estoque/vendas/<id>/cancelar`
- **Método**: `POST`
- **Descrição**: Cancela uma venda e devolve itens ao estoque (apenas admin/gerente)
- **Resposta de Sucesso**:

  ```json
  {
    "message": "Venda cancelada com sucesso!"
  }
  ```

### Página de Vendas

- **URL**: `/estoque/vendas/page`
- **Método**: `GET`
- **Descrição**: Renderiza a página de listagem de vendas

### Nova Venda (Página)

- **URL**: `/estoque/vendas/nova`
- **Método**: `GET`
- **Descrição**: Renderiza a página para realizar uma nova venda

## Fornecedores

### Listar Fornecedores

- **URL**: `/fornecedores`
- **Método**: `GET`
- **Descrição**: Lista todos os fornecedores cadastrados

### Adicionar Fornecedor

- **URL**: `/fornecedores`
- **Método**: `POST`
- **Corpo da Requisição**:

  ```json
  {
    "nome": "Novo Fornecedor",
    "cnpj": "12.345.678/0001-90",
    "email": "contato@fornecedor.com",
    "telefone": "(99) 99999-9999",
    "endereco": "Rua Exemplo, 123",
    "ativo": true
  }
  ```

### Detalhar Fornecedor

- **URL**: `/fornecedores/<id>`
- **Método**: `GET`
- **Descrição**: Retorna detalhes de um fornecedor específico

### Atualizar Fornecedor

- **URL**: `/fornecedores/<id>`
- **Método**: `PUT`
- **Descrição**: Atualiza informações de um fornecedor

### Excluir Fornecedor

- **URL**: `/fornecedores/<id>`
- **Método**: `DELETE`
- **Descrição**: Exclui um fornecedor (se não tiver produtos associados)

### Produtos por Fornecedor

- **URL**: `/fornecedores/<id>/produtos`
- **Método**: `GET`
- **Descrição**: Lista produtos associados a um fornecedor específico

## Dashboard

### Estatísticas

- **URL**: `/api/estatisticas`
- **Método**: `GET`
- **Descrição**: Retorna estatísticas gerais para o dashboard
- **Resposta de Sucesso**:

  ```json
  {
    "total_produtos": 150,
    "valor_estoque": 45000.00,
    "vendas_hoje": 12,
    "receita_hoje": 3500.00,
    "produtos_estoque_baixo": 8
  }
  ```

### Produtos com Estoque Baixo

- **URL**: `/api/produtos/estoque-baixo`
- **Método**: `GET`
- **Descrição**: Lista produtos com estoque abaixo do mínimo
- **Resposta de Sucesso**:

  ```json
  {
    "produtos": [
      {
        "id": 5,
        "nome": "Produto X",
        "estoque": 3,
        "estoque_minimo": 10
      }
    ]
  }
  ```

### Dados para Gráfico de Movimentação

- **URL**: `/estoque/movimentacoes/grafico`
- **Método**: `GET`
- **Descrição**: Retorna dados para gerar gráfico de movimentações
- **Resposta de Sucesso**:

  ```json
  {
    "labels": ["01/04", "02/04", "03/04"],
    "entradas": [15, 20, 10],
    "saidas": [8, 12, 5]
  }
  ```

## Relatórios

### Relatórios Gerais

- **URL**: `/relatorios`
- **Método**: `GET`
- **Descrição**: Retorna dados para relatórios de produtos mais e menos vendidos
- **Resposta de Sucesso**:

  ```json
  {
    "mais_vendidos": [
      {
        "id": 1,
        "nome": "Produto Popular",
        "quantidade": 250,
        "estoque": 35
      }
    ],
    "menos_vendidos": [
      {
        "id": 10,
        "nome": "Produto Raro",
        "quantidade": 2,
        "estoque": 45
      }
    ]
  }
  ```
