
// api/index.js

import axios from 'axios'

const URL = 'http://127.0.0.1:5000'

// ------------------------------
// Auth interface
// ------------------------------

export function postSignup(userData) {
  return axios.post(`${URL}/signup`, userData)
}

export function postLogin(userData) {
  return axios.post(`${URL}/login`, userData)
}


// ------------------------------
// Main interface
// ------------------------------

export function getGroupNames() {
  return axios.get(`${URL}/groups/names`)
}

export function postGroup(group_name, group_resource, jwt) {
  return axios.post(`${URL}/groups/${group_name}`, group_resource, { headers: { Authorization: `Bearer: ${jwt}` } })
}

export function getGroup(group_name, jwt) {
  return axios.get(`${URL}/groups/${group_name}`, { headers: { Authorization: `Bearer: ${jwt}` } })
}

export function postMatch(team1, team2, jwt) {
  return axios.post(`${URL}/match`, { params: { team1: team1, team2: team2 } }, { headers: { Authorization: `Bearer: ${jwt}` } })
}

export function getMatch(team1, team2) {
  return axios.get(`${URL}/match`, { params: { team1: team1, team2: team2 } })
}

export function getScoreBoard(jwt) {
  return axios.get(`${URL}/score_board`, { headers: { Authorization: `Bearer: ${jwt}` } })
}
