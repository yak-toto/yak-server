
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

export function getGroupNames(jwt) {
  return axios.get(`${URL}/groups/names`, { headers: { Authorization: `Bearer: ${jwt}` } })
}

export function getGroup(group_name, jwt) {
  return axios.get(`${URL}/groups/${group_name}`, { headers: { Authorization: `Bearer: ${jwt}` } })
}

export function postMatch(match_id, match_resource, jwt) {
  return axios.post(`${URL}/match/${match_id}`, match_resource, { headers: { Authorization: `Bearer: ${jwt}` } })
}

export function getMatch(team1, team2) {
  return axios.get(`${URL}/match`, { params: { team1: team1, team2: team2 } })
}

export function getScoreBoard(jwt) {
  return axios.get(`${URL}/score_board`, { headers: { Authorization: `Bearer: ${jwt}` } })
}
