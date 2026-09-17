import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'

export default function CorretorList({ corretores, onEdit, onDelete }) {
  if (corretores.length === 0) {
    return (
      <Typography color="text.secondary" textAlign="center" py={4}>
        Nenhum corretor cadastrado.
      </Typography>
    )
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell><strong>Nome</strong></TableCell>
            <TableCell><strong>Email</strong></TableCell>
            <TableCell><strong>Telefone</strong></TableCell>
            <TableCell align="center"><strong>Ações</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {corretores.map(c => (
            <TableRow key={c.id} hover>
              <TableCell>{c.nome}</TableCell>
              <TableCell>{c.email}</TableCell>
              <TableCell>{c.telefone}</TableCell>
              <TableCell align="center">
                <Tooltip title="Editar">
                  <IconButton size="small" onClick={() => onEdit(c)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Excluir">
                  <IconButton size="small" color="error" onClick={() => onDelete(c.id)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
