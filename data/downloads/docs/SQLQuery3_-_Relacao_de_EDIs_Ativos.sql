/****** Script de Busca de EDIs Ativos ******/

SELECT
    C.Nome_FantasiaCliente,
    C.Nome_RazaoSocialCliente,
    CEA.Nome_ClienteEdiAgenda,
    CEA.Descricao_ClienteEdiAgenda,

    -- Separação dos e-mails principais (Email_EnvioEdi)
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[1]', 'varchar(100)') AS Email_Principal_1,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[2]', 'varchar(100)') AS Email_Principal_2,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[3]', 'varchar(100)') AS Email_Principal_3,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[4]', 'varchar(100)') AS Email_Principal_4,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[5]', 'varchar(100)') AS Email_Principal_5,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[6]', 'varchar(100)') AS Email_Principal_6,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdi, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[7]', 'varchar(100)') AS Email_Principal_7,

    -- Separação dos e-mails em cópia (Email_EnvioEdiCc)
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[1]', 'varchar(100)') AS Email_Copia_1,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[2]', 'varchar(100)') AS Email_Copia_2,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[3]', 'varchar(100)') AS Email_Copia_3,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[4]', 'varchar(100)') AS Email_Copia_4,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[5]', 'varchar(100)') AS Email_Copia_5,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[6]', 'varchar(100)') AS Email_Copia_6,
    CAST('<M>' + REPLACE(ISNULL(CEL.Email_EnvioEdiCc, ''), ';', '</M><M>') + '</M>' AS XML).value('/M[7]', 'varchar(100)') AS Email_Copia_7,
    
    CEA.Opcao_StatusAgenda
FROM
    [LuftInforma].[dbo].[ClienteEdiAgenda] AS CEA
INNER JOIN
    [LuftInforma].[dbo].[ClienteEdiLayOut] AS CEL ON CEA.Codigo_ClienteEdiLayOut = CEL.Codigo_ClienteEdiLayOut
INNER JOIN
    [LuftInforma].[dbo].[Cliente] AS C ON CEL.Codigo_Cliente = C.Codigo_Cliente
WHERE
    (
        CEA.Nome_ClienteEdiAgenda LIKE '%CONEMB%' OR
        CEA.Nome_ClienteEdiAgenda LIKE '%OCOREN%' OR
        CEA.Nome_ClienteEdiAgenda LIKE '%DOCCOB%'
    )
    AND CEA.Opcao_StatusAgenda = 1 -- Define se é EDI ativo com '1' se quiser os inativos inserir '0'.
ORDER BY
    C.Nome_FantasiaCliente, CEA.Nome_ClienteEdiAgenda;